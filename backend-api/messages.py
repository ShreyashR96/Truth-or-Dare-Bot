import random

# --- Message Templates ---

NEW_GAME_MESSAGE = """
🎉 *A New Game Has Begun\\!* 🎉

*Game:* {game_name}
*Admin:* {admin_name}

Players, click the button below to join the fun\\!
The admin can start the game with `/startgame` once at least 2 players have joined\\.
"""

HELP_MESSAGE = """
👋 *Truth & Dare Bot Help Guide*

Here are all the commands you can use to play the game and check stats\\.

*👑 Admin Commands*
`• /newgame` \\- Creates a new game lobby\\.
`• /startgame` \\- Starts the game after players have joined\\.
`• /stop` \\- Ends the current game and shows final scores\\.
`• /groupid` \\- Gets the unique ID for this group\\.

*👤 Player Commands*
`• /scores` \\- View the current scoreboard\\.
`• /players` \\- See who is in the game\\.
`• /groupstats` \\- View all\\-time stats for this group\\.
`• /myid` \\- Get your personal user ID \\(in a private chat with me\\)\\.
`• /help` \\- Shows this help message\\.

*Scoring System*
*✅ Complete Task:* `+5 points`
*🔄 Change Task:* `-2 points`
*⏭️ Skip Task:* `-6 points`
"""

PRIVATE_START_MESSAGE = """
👋 Hello\\! I'm the Truth or Dare Bot\\.

My main purpose is to run games inside Telegram groups\\. Add me to a group with your friends to get started\\!

You can use the following commands in this private chat:
`• /myid` \\- Get your unique User ID to check your stats on the website\\.
`• /help` \\- See a list of all available commands\\.
"""

GROUP_STATS_MESSAGE = """
📈 *Group Statistics for {title}*

*🎮 Total Games Played:* {total_games}
*🤔 Total Truths:* {total_truths}
*😈 Total Dares:* {total_dares}
*🌟 Highest Score Ever:* {highest_score}
*👥 Unique Players:* {unique_players}
"""


# --- Dynamic Messages ---

ADJECTIVES = ["Epic", "Cosmic", "Wild", "Crazy", "Super", "Magic", "Mystic", "Awesome"]
NOUNS = ["Quest", "Adventure", "Challenge", "Party", "Mission", "Journey", "Showdown"]

TRUTH_MESSAGES = [
    "🤔 Time for some truth\\! Be honest\\.\\.\\.",
    "🎯 Truth time\\! No escaping this one\\.\\.\\.",
    "🌟 Let's hear the truth and nothing but the truth\\!",
    "🎭 Time to reveal your secrets\\.\\.\\.",
]

DARE_MESSAGES = [
    "🔥 Ready for a spicy dare?",
    "⚡️ Lightning dare coming up\\!",
    "🎪 Time for some circus\\-level action\\!",
    "🎭 Show time\\! Your dare awaits\\.\\.\\.",
]

SKIP_MESSAGES = [
    "😅 Chickened out this time\\!",
    "⏭️ Fast forward activated\\!",
    "🏃‍♂️ Running away from this one\\!",
]

SUCCESS_MESSAGES = [
    "🌟 Absolutely brilliant\\!",
    "🎉 You nailed it\\!",
    "🏆 Champion move\\!",
    "✨ Spectacular job\\!",
]

NEXT_PLAYER_MESSAGES = [
    "🎲 The dice has been rolled\\! Next up is {player_name}\\!",
    " spotlight is now on {player_name}\\!",
    "✨ Get ready, {player_name}, it's your turn to shine\\!",
    "🎯 Target locked on {player_name}\\! What's your choice?",
]

GAME_START_MESSAGES = [
    "🎪 The circus is open\\! Let the games begin\\!",
    "🎭 The show is starting\\! Good luck to all players\\!",
    "🚀 Blast off\\! The game has officially started\\!",
]

GAME_END_MESSAGES = [
    "🎪 The circus is closing for now\\! Thanks for playing\\!",
    "🎭 That's a wrap on this show\\! What a performance\\!",
    "🌟 The stars fade but the memories remain\\!",
]

def get_truth_message(player_name):
    return random.choice(TRUTH_MESSAGES) + f"\n👤 {player_name}"

def get_dare_message(player_name):
    return random.choice(DARE_MESSAGES) + f"\n👤 {player_name}"

def get_skip_message(player_name):
    return f"{random.choice(SKIP_MESSAGES)}\n👤 {player_name}"

def get_success_message(player_name, points):
    return f"{random.choice(SUCCESS_MESSAGES)}\n👤 {player_name}\n💫 +{points} points\\!"

def get_next_player_message(player_name):
    return random.choice(NEXT_PLAYER_MESSAGES).format(player_name=player_name)

def get_game_start_message():
    return random.choice(GAME_START_MESSAGES)

def get_game_end_message():
    return random.choice(GAME_END_MESSAGES)
