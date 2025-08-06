import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from datetime import datetime
import logging
import certifi # <-- Import the new library

# Load environment variables from .env file
load_dotenv()

# --- Logging ---
logger = logging.getLogger(__name__)

class Database:
    """
    Handles all interactions with the MongoDB database.
    """
    def __init__(self):
        """
        Initializes and validates the database connection.
        """
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("DB_NAME", "truth_dare_bot")
        
        if not mongo_uri:
            logger.critical("MONGODB_URI not found in environment variables. Bot cannot start.")
            raise ValueError("MONGODB_URI not found in environment variables.")
        
        try:
            # --- FIX: Use certifi and allow invalid certificates to bypass SSL handshake issues ---
            ca = certifi.where()
            self.client = MongoClient(mongo_uri, tls=True, tlsCAFile=ca, tlsAllowInvalidCertificates=True, serverSelectionTimeoutMS=5000)
            
            # The ismaster command is cheap and does not require auth. It's a quick way to verify the connection.
            self.client.admin.command('ismaster')
            
            self.db = self.client[db_name]
            
            # Collections
            self.games = self.db["games"]
            self.groups = self.db["groups"]
            self.users = self.db["users"]
            
            logger.info("✅ Database connected successfully.")
            
        except ConnectionFailure as e:
            logger.critical(f"❌ Could not connect to MongoDB: {e}. Please check your MONGODB_URI and ensure the server is running.")
            raise ConnectionError(f"Database connection failed: {e}") from e
        except Exception as e:
            logger.critical(f"An unexpected error occurred during database initialization: {e}")
            raise

    # --- Game Management ---

    def get_game(self, chat_id: int):
        """Fetches the current game state for a chat."""
        return self.games.find_one({"_id": chat_id})

    def create_game(self, chat_id: int, game_data: dict):
        """Creates a new game document in the database."""
        game_data["_id"] = chat_id
        return self.games.insert_one(game_data)

    def update_game(self, chat_id: int, updates: dict):
        """Updates an active game's state using $set."""
        return self.games.update_one({"_id": chat_id}, {"$set": updates})

    def delete_game(self, chat_id: int):
        """Removes a game document after it has ended."""
        return self.games.delete_one({"_id": chat_id})

    # --- Statistics Management ---
    
    def get_group_stats(self, chat_id: int):
        """Retrieves statistics for a specific group."""
        return self.groups.find_one({"_id": chat_id})

    def update_stats_on_game_end(self, chat_id: int, chat_title: str, game_data: dict, winner_name: str):
        """Updates group and user statistics when a game ends."""
        self.groups.update_one({"_id": chat_id}, {"$set": {"title": chat_title}}, upsert=True)
        
        game_history_entry = {
            "game_id": game_data["game_id"], "game_name": game_data["game_name"],
            "start_time": game_data.get("start_time"), "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "players": len(game_data.get("players", [])), "winner": winner_name,
            "scores": { str(pid): game_data["scores"].get(str(pid), 0) for pid in game_data["players"] }
        }
        highest_score_in_game = max(game_data["scores"].values()) if game_data["scores"] else 0
        
        self.groups.update_one(
            {"_id": chat_id},
            {
                "$inc": { "total_games": 1, "total_truths": game_data.get("truth_count", 0), "total_dares": game_data.get("dare_count", 0) },
                "$max": {"highest_score": highest_score_in_game},
                "$push": { "game_history": { "$each": [game_history_entry], "$slice": -10 } },
                "$addToSet": {"all_players": {"$each": [str(p) for p in game_data.get("players", [])]}},
                "$set": {"last_played": datetime.now()}
            },
            upsert=True
        )
        for player_id in game_data.get("players", []):
            self.update_player_stats(player_id, chat_id, game_data)

    def update_player_stats(self, user_id: int, chat_id: int, game_data: dict):
        player_id_str = str(user_id)
        player_score = game_data.get("scores", {}).get(player_id_str, 0)
        player_game_stats = game_data.get("player_stats", {}).get(player_id_str, {})
        
        self.users.update_one(
            {"_id": user_id},
            {
                "$inc": {
                    "games_played": 1, "total_score": player_score,
                    "total_truths": player_game_stats.get('truths', 0),
                    "total_dares": player_game_stats.get('dares', 0),
                    "total_skips": player_game_stats.get('skips', 0),
                    "total_changes": player_game_stats.get('changes', 0),
                },
                "$max": {"highest_score": player_score},
                "$set": {"last_played": datetime.now()},
                "$addToSet": {"groups_played": chat_id}
            },
            upsert=True
        )

    async def update_user_info(self, user):
        self.users.update_one(
            {"_id": user.id},
            {"$set": { "username": user.username, "first_name": user.first_name } },
            upsert=True
        )

# Create a single instance of the database to be used by the bot
db = Database()
