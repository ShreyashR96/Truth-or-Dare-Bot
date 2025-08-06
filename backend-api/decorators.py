from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

# --- Permission Decorators ---

def is_admin(func):
    """
    Decorator to check if the user is a group administrator or creator.
    """
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_chat.type in ["group", "supergroup"]:
            await update.message.reply_text("This command can only be used in groups.")
            return
            
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        try:
            member = await context.bot.get_chat_member(chat_id, user_id)
            if member.status not in ['administrator', 'creator']:
                await update.message.reply_text("❌ You must be a group admin to use this command.")
                return
        except Exception as e:
            await update.message.reply_text("❌ Could not verify your admin status. Make sure the bot has admin rights.")
            print(f"Error checking admin status: {e}")
            return
            
        return await func(update, context, *args, **kwargs)
    return wrapped

def game_is_active(is_active: bool):
    """
    Decorator to check if a game is active or inactive.
    - is_active=True: Command requires an active game.
    - is_active=False: Command requires no active game.
    """
    def decorator(func):
        @wraps(func)
        async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            from database import db # Local import to avoid circular dependency
            chat_id = update.effective_chat.id
            game_exists = db.get_game(chat_id) is not None

            if is_active and not game_exists:
                await update.message.reply_text("There is no active game. Start one with /newgame.")
                return
            
            if not is_active and game_exists:
                await update.message.reply_text("A game is already in progress! Use /stop to end it first.")
                return

            return await func(update, context, *args, **kwargs)
        return wrapped
    return decorator
