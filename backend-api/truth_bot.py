import random
import json
import os
import logging
from datetime import datetime
from collections import deque
from dotenv import load_dotenv
from typing import tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.error import BadRequest

# Import local modules
from database import db
import messages
from decorators import is_admin, game_is_active

# --- Logging Configuration ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Game Logic Class ---
class TruthDareGame:
    def __init__(self):
        self.truths = self._load_questions('data/truth.json')
        self.dares = self._load_questions('data/dare.json')

    def _load_questions(self, file_path: str) -> list:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading {file_path}: {e}")
            return []

    def get_random_question(self, choice: str, used_questions: list) -> tuple[str, list]:
        question_list = self.truths if choice == "truth" else self.dares
        used_set = set(used_questions)
        
        available = [q for q in question_list if q not in used_set]
        
        if not available:
            logger.warning(f"All {choice} questions used. Resetting.")
            used_questions = []
            available = question_list

        question = random.choice(available)
        used_questions.append(question)
        return question, used_questions

game_logic = TruthDareGame()

# --- Utility Functions ---
def escape_markdown_v2(text: str) -> str:
    """Helper function to escape text for Telegram MarkdownV2."""
    if not text: return ""
    # We need to convert the input to string because numbers can be passed here
    text = str(text)
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in text)

async def get_player_name_and_mention(context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int) -> tuple[str, str]:
    """Gets a player's name (prioritizing username) and a markdown mention string."""
    name = None
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        await db.update_user_info(member.user)
        # Prioritize username, then first_name
        name = member.user.username or member.user.first_name
    except Exception as e:
        logger.warning(f"Could not fetch user {user_id} via API: {e}. Falling back to DB.")
        user_doc = db.users.find_one({"_id": user_id})
        if user_doc:
            name = user_doc.get("username") or user_doc.get("first_name")

    if not name:
        name = f"Player_{user_id}"

    safe_name = escape_markdown_v2(str(name))
    mention = f"[{safe_name}](tg://user?id={user_id})"
    return name, mention

# --- Global Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text("🤖 Oops! Something went wrong. The developers have been notified.")
        except BadRequest:
            logger.error("Failed to send error message to user.")

# --- Command Handlers (Admin)---
@is_admin
@game_is_active(False)
async def new_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    game_name = f"{random.choice(messages.ADJECTIVES)} {random.choice(messages.NOUNS)} #{random.randint(1000, 9999)}"
    game_id = f"{datetime.now().strftime('%y%m%d%H%M')}-{random.randint(100, 999)}"

    game_data = {
        "_id": chat_id, "game_id": game_id, "game_name": game_name, "admin_id": user.id,
        "players": [], "scores": {}, "player_stats": {}, "player_queue": [],
        "current_player": None, "current_choice": None,
        "used_questions": {"truth": [], "dare": []},
        "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "waiting"
    }
    db.create_game(chat_id, game_data)
    await db.update_user_info(user)

    keyboard = [[InlineKeyboardButton("Join Game 🎮", callback_data="join_game")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    admin_name = user.username or user.first_name or "Admin"
    
    message = messages.NEW_GAME_MESSAGE.format(
        game_name=escape_markdown_v2(game_name), 
        admin_name=escape_markdown_v2(admin_name)
    )
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2)
    logger.info(f"New game '{game_name}' created in chat {chat_id} by {user.id}")

@is_admin
@game_is_active(True)
async def start_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_data = db.get_game(chat_id)
    if len(game_data["players"]) < 2:
        await update.message.reply_text("You need at least 2 players to start!")
        return
    if game_data["status"] == "playing":
        await update.message.reply_text("The game has already started!")
        return
    random.shuffle(game_data["players"])
    db.update_game(chat_id, {"status": "playing", "player_queue": game_data["players"]})
    await update.message.reply_text(messages.get_game_start_message(), parse_mode=ParseMode.MARKDOWN_V2)
    await select_next_player(context, chat_id)

@is_admin
@game_is_active(True)
async def stop_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    game_data = db.get_game(chat_id)
    
    if "game_id" not in game_data:
        game_data["game_id"] = f"legacy-{datetime.now().strftime('%y%m%d%H%M%S')}"
    if "game_name" not in game_data:
        game_data["game_name"] = "Legacy Game"

    winner_name = "No winner"
    scores_dict = game_data.get("scores", {})
    if scores_dict:
        winner_id = int(max(scores_dict, key=scores_dict.get))
        name, _ = await get_player_name_and_mention(context, chat_id, winner_id)
        winner_name = name

    db.update_stats_on_game_end(chat_id, chat_title, game_data, winner_name)

    final_message = f"🏁 *Game Over\\!* 🏁\n\nThanks for playing *{escape_markdown_v2(game_data['game_name'])}*\\!\n\n🏆 *Final Scoreboard* 🏆\n"
    if not scores_dict:
        final_message += "No scores were recorded in this game\\."
    else:
        sorted_players = sorted(scores_dict.items(), key=lambda item: item[1], reverse=True)
        for i, (player_id, score) in enumerate(sorted_players):
            try:
                name, _ = await get_player_name_and_mention(context, chat_id, int(player_id))
                emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "•"
                # --- FIX: Escape the score as well ---
                final_message += f"{emoji} {escape_markdown_v2(name)}: {escape_markdown_v2(score)} points\n"
            except Exception as e:
                logger.error(f"Could not process score for player {player_id} in stop_game: {e}")
                final_message += f"• Player_{player_id}: {escape_markdown_v2(score)} points \\(Could not fetch name\\)\n"

    final_message += f"\nUse `/groupstats` to see all\\-time records\\!\n{messages.get_game_end_message()}"
    try:
        await update.message.reply_text(final_message, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Failed to send final scoreboard for chat {chat_id}: {e}")
        await update.message.reply_text("Game has been stopped. There was an issue displaying the final scores.")
    db.delete_game(chat_id)
    logger.info(f"Game stopped and stats saved for chat {chat_id}")

@is_admin
async def group_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = (
        f"🔑 *This Group's ID*\n\n"
        f"Here is the ID for this group\\. You can use this to check your group's stats on our website\\.\n\n"
        f"`{chat_id}`\n\n"
        f"_Tap the ID above to copy it\\._"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

# --- Command Handlers (Public) ---
@game_is_active(True)
async def scores_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_data = db.get_game(chat_id)
    message = "📊 *Current Scores*\n\n"
    if not game_data.get("scores"):
        return await update.message.reply_text("No scores yet. The game has just started!")
        
    sorted_players = sorted(game_data["scores"].items(), key=lambda item: item[1], reverse=True)

    for player_id, score in sorted_players:
        name, _ = await get_player_name_and_mention(context, chat_id, int(player_id))
        # --- FIX: Escape the score as well ---
        message += f"• {escape_markdown_v2(name)}: {escape_markdown_v2(score)} points\n"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

@game_is_active(True)
async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game_data = db.get_game(chat_id)
    message = f"👥 *Players in {escape_markdown_v2(game_data['game_name'])}* ({len(game_data['players'])})\n\n"
    for player_id in game_data["players"]:
        name, _ = await get_player_name_and_mention(context, chat_id, player_id)
        message += f"• {escape_markdown_v2(name)}\n"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def group_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat.type in ["group", "supergroup"]:
        return await update.message.reply_text("This command can only be used in groups.")
    chat_id = update.effective_chat.id
    stats = db.get_group_stats(chat_id)
    if not stats:
        return await update.message.reply_text("No games have been played yet. Start one with `/newgame`!")
    message = messages.GROUP_STATS_MESSAGE.format(
        title=escape_markdown_v2(update.effective_chat.title),
        total_games=stats.get('total_games', 0),
        total_truths=stats.get('total_truths', 0),
        total_dares=stats.get('total_dares', 0),
        highest_score=stats.get('highest_score', 0),
        unique_players=len(stats.get('all_players', []))
    )
    if stats.get("game_history"):
        message += "\n📜 *Recent Game History:*\n"
        for game_entry in reversed(stats["game_history"][-3:]):
            dt = datetime.strptime(game_entry['start_time'], "%Y-%m-%d %H:%M:%S")
            date_str = dt.strftime("%b %d")
            winner = game_entry.get("winner", "N/A")
            message += f"  \\- *{escape_markdown_v2(game_entry['game_name'])}* on {date_str} \\(Winner: {escape_markdown_v2(winner)}\\)\n"
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /start command differently in private vs group chats."""
    if update.effective_chat.type == "private":
        await update.message.reply_text(messages.PRIVATE_START_MESSAGE, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await update.message.reply_text("👋 Bot is active! Use `/help` to see all commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the help message."""
    await update.message.reply_text(messages.HELP_MESSAGE, parse_mode=ParseMode.MARKDOWN_V2)

async def my_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the /myid command in private chat."""
    if update.effective_chat.type != "private":
        await update.message.reply_text("This command only works in a private chat with me.")
        return
    user_id = update.effective_user.id
    message = (
        "✨ *Your Unique User ID*\n\n"
        "Here is your personal Telegram ID\\. You can use this to check your stats on our website\\.\n\n"
        f"`{user_id}`\n\n"
        "_Tap the ID above to copy it\\._"
    )
    await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN_V2)

# --- Callback Query Handlers ---
async def join_game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user = query.from_user
    game_data = db.get_game(chat_id)
    if not game_data:
        await query.answer("This game has ended.", show_alert=True)
        try: await query.edit_message_text("This game has ended or been cancelled.")
        except BadRequest: pass
        return
    if user.id in game_data["players"]:
        return await query.answer("You're already in the game!", show_alert=True)
    
    player_id_str = str(user.id)
    db.games.update_one(
        {"_id": chat_id},
        {
            "$push": {"players": user.id},
            "$set": {
                f"scores.{player_id_str}": 0,
                f"player_stats.{player_id_str}": {"truths": 0, "dares": 0, "skips": 0, "changes": 0}
            }
        }
    )
    await db.update_user_info(user)
    await query.answer("You have joined the game!")
    
    player_name = user.username or user.first_name or f"Player_{user.id}"
    await query.message.reply_text(f"✅ {escape_markdown_v2(player_name)} has joined the game\\!", parse_mode=ParseMode.MARKDOWN_V2)

async def choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    choice = query.data
    game_data = db.get_game(chat_id)

    if not game_data or user_id != game_data.get("current_player"):
        return await query.answer("It's not your turn!", show_alert=True)

    question, new_used = game_logic.get_random_question(choice, game_data["used_questions"][choice])
    db.update_game(chat_id, {
        f"used_questions.{choice}": new_used,
        "current_choice": choice
    })

    keyboard = [
        [InlineKeyboardButton("✅ Mark as Complete", callback_data="complete")],
        [InlineKeyboardButton("⏭️ Skip", callback_data="skip"), InlineKeyboardButton("🔄 Change", callback_data="change_task")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    player_name, _ = await get_player_name_and_mention(context, chat_id, user_id)
    message_template = messages.get_truth_message if choice == "truth" else messages.get_dare_message
    
    await query.edit_message_text(
        f"{message_template(escape_markdown_v2(player_name))}\n\n*{choice.upper()}:* {escape_markdown_v2(question)}",
        reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN_V2
    )

async def completion_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    action = query.data
    game_data = db.get_game(chat_id)
    if not game_data: return await query.answer("Game not found.", show_alert=True)

    if action == "complete":
        member = await context.bot.get_chat_member(chat_id, query.from_user.id)
        if member.status not in ['administrator', 'creator']:
            return await query.answer("Only a group admin can mark tasks as complete!", show_alert=True)
    elif query.from_user.id != game_data.get("current_player"):
        return await query.answer("It's not your turn to do this!", show_alert=True)

    current_player_id = game_data["current_player"]
    player_id_str = str(current_player_id)
    player_name, _ = await get_player_name_and_mention(context, chat_id, current_player_id)
    
    updates = {}
    completion_message = ""

    if action == "complete":
        choice = game_data["current_choice"]
        updates["$inc"] = {
            f"scores.{player_id_str}": 5,
            f"player_stats.{player_id_str}.{choice}s": 1,
            f"{choice}_count": 1
        }
        completion_message = messages.get_success_message(escape_markdown_v2(player_name), 5)
    
    elif action == "skip":
        updates["$inc"] = {
            f"scores.{player_id_str}": -6,
            f"player_stats.{player_id_str}.skips": 1
        }
        completion_message = messages.get_skip_message(escape_markdown_v2(player_name))
    
    elif action == "change_task":
        choice = game_data["current_choice"]
        question, new_used = game_logic.get_random_question(choice, game_data["used_questions"][choice])
        updates["$inc"] = {
            f"scores.{player_id_str}": -2,
            f"player_stats.{player_id_str}.changes": 1
        }
        updates["$set"] = {f"used_questions.{choice}": new_used}
        
        db.games.update_one({"_id": chat_id}, updates)
        await query.answer("Task changed! -2 points.", show_alert=True)
        keyboard = [[InlineKeyboardButton("✅ Mark as Complete", callback_data="complete")], [InlineKeyboardButton("⏭️ Skip", callback_data="skip"), InlineKeyboardButton("🔄 Change", callback_data="change_task")]]
        return await query.edit_message_text(
            f"{messages.get_dare_message(escape_markdown_v2(player_name))}\n\n*{choice.upper()}:* {escape_markdown_v2(question)}",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN_V2
        )

    new_game_data = db.games.find_one_and_update({"_id": chat_id}, updates, return_document=True)
    new_score = new_game_data["scores"][player_id_str]
    await query.edit_message_text(f"{completion_message}\nNew score: {escape_markdown_v2(new_score)}")
    await select_next_player(context, chat_id)

# --- Core Game Flow ---
async def select_next_player(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    game_data = db.get_game(chat_id)
    if not game_data or game_data["status"] != "playing": return

    player_queue = deque(game_data["player_queue"])
    player_queue.rotate(-1)
    next_player_id = player_queue[0]
    
    db.update_game(chat_id, {"current_player": next_player_id, "player_queue": list(player_queue)})
    
    name, mention = await get_player_name_and_mention(context, chat_id, next_player_id)
    keyboard = [[InlineKeyboardButton("🤔 Truth", callback_data="truth"), InlineKeyboardButton("😈 Dare", callback_data="dare")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = messages.get_next_player_message(player_name=mention)
    
    await context.bot.send_message(
        chat_id, 
        text=f"\\-\\-\\- Next Turn \\-\\-\\-\n{message}", 
        reply_markup=reply_markup, 
        parse_mode=ParseMode.MARKDOWN_V2
    )

# --- Main Application Setup ---
def main():
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logger.critical("TELEGRAM_TOKEN environment variable not set!")
        return

    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("myid", my_id_command))
    application.add_handler(CommandHandler("groupid", group_id_command))
    application.add_handler(CommandHandler("newgame", new_game_command))
    application.add_handler(CommandHandler("startgame", start_game_command))
    application.add_handler(CommandHandler("stop", stop_game_command))
    application.add_handler(CommandHandler("scores", scores_command))
    application.add_handler(CommandHandler("players", players_command))
    application.add_handler(CommandHandler("groupstats", group_stats_command))

    application.add_handler(CallbackQueryHandler(join_game_callback, pattern="^join_game$"))
    application.add_handler(CallbackQueryHandler(choice_callback, pattern="^(truth|dare)$"))
    application.add_handler(CallbackQueryHandler(completion_callback, pattern="^(complete|skip|change_task)$"))
    
    application.add_error_handler(error_handler)
    
    logger.info("Bot is starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
