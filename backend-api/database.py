import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

class Database:
    """
    Handles all interactions with the Supabase database.
    """
    def __init__(self):
        """
        Initializes the Supabase client.
        """
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            logger.critical("SUPABASE_URL or SUPABASE_KEY not found. Bot cannot start.")
            raise ValueError("Supabase credentials not found in environment variables.")

        try:
            self.supabase: Client = create_client(url, key)
            # A simple check to see if we can list tables
            self.supabase.table('users').select('id', head=True).execute()
            logger.info("✅ Supabase connected successfully.")
        except Exception as e:
            logger.critical(f"❌ Could not connect to Supabase: {e}")
            raise ConnectionError(f"Supabase connection failed: {e}") from e

    # --- Game Management ---

    def get_game(self, chat_id: int):
        """Fetches the current game state for a chat."""
        response = self.supabase.table('games').select('game_data').eq('id', chat_id).single().execute()
        return response.data.get('game_data') if response.data else None

    def create_game(self, chat_id: int, game_data: dict):
        """Creates or updates a new game document in the database."""
        # Use upsert to handle both creation and updates seamlessly
        return self.supabase.table('games').upsert({
            'id': chat_id,
            'game_data': json.dumps(game_data) # Supabase client expects JSON as a string
        }).execute()

    def update_game(self, chat_id: int, updates: dict):
        """Updates an active game's state by fetching, updating, and saving."""
        current_game_data = self.get_game(chat_id)
        if current_game_data:
            current_game_data.update(updates)
            return self.create_game(chat_id, current_game_data) # Use upsert to update

    def delete_game(self, chat_id: int):
        """Removes a game document after it has ended."""
        return self.supabase.table('games').delete().eq('id', chat_id).execute()

    # --- Statistics Management ---

    def update_stats_on_game_end(self, chat_id: int, chat_title: str, game_data: dict, winner_name: str):
        """Updates group and user statistics when a game ends."""
        # --- 1. Update Group Info ---
        group_response = self.supabase.table('groups').select('*').eq('id', chat_id).single().execute()
        group = group_response.data or {}

        game_history = group.get('game_history', []) or []
        game_history.append({
            "game_id": game_data["game_id"], "game_name": game_data["game_name"],
            "start_time": game_data.get("start_time"), "end_time": datetime.now().isoformat(),
            "players": len(game_data.get("players", [])), "winner": winner_name,
            "scores": { str(pid): game_data["scores"].get(str(pid), 0) for pid in game_data["players"] }
        })

        highest_score_in_game = max(game_data["scores"].values()) if game_data["scores"] else 0
        
        self.supabase.table('groups').upsert({
            'id': chat_id,
            'title': chat_title,
            'total_games': group.get('total_games', 0) + 1,
            'highest_score': max(group.get('highest_score', 0), highest_score_in_game),
            'all_players': list(set((group.get('all_players') or []) + [str(p) for p in game_data.get("players", [])])),
            'game_history': json.dumps(game_history[-10:]), # Keep last 10
            'last_played': datetime.now().isoformat()
        }).execute()

        # --- 2. Update Player Info ---
        for player_id in game_data.get("players", []):
            self.update_player_stats(player_id, chat_id, game_data)

    def update_player_stats(self, user_id: int, chat_id: int, game_data: dict):
        """Updates the global statistics for a single player."""
        user_response = self.supabase.table('users').select('*').eq('id', user_id).single().execute()
        user = user_response.data or {}

        player_id_str = str(user_id)
        player_score = game_data.get("scores", {}).get(player_id_str, 0)
        player_game_stats = game_data.get("player_stats", {}).get(player_id_str, {})
        
        groups_played = user.get('groups_played', []) or []
        if chat_id not in groups_played:
            groups_played.append(chat_id)

        self.supabase.table('users').upsert({
            'id': user_id,
            'games_played': user.get('games_played', 0) + 1,
            'total_score': user.get('total_score', 0) + player_score,
            'highest_score': max(user.get('highest_score', 0), player_score),
            'total_truths': user.get('total_truths', 0) + player_game_stats.get('truths', 0),
            'total_dares': user.get('total_dares', 0) + player_game_stats.get('dares', 0),
            'total_skips': user.get('total_skips', 0) + player_game_stats.get('skips', 0),
            'total_changes': user.get('total_changes', 0) + player_game_stats.get('changes', 0),
            'groups_played': json.dumps(groups_played),
            'last_played': datetime.now().isoformat()
        }).execute()

    async def update_user_info(self, user):
        """Updates user information like username and first_name."""
        self.supabase.table('users').upsert({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name
        }).execute()

db = Database()
