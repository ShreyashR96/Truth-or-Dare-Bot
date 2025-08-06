import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from dotenv import load_dotenv
from typing import List, Dict, Any

# --- Load Environment Variables ---
load_dotenv()

# --- Database Connection ---
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "truth_dare_bot")

if not MONGO_URI:
    raise Exception("MONGODB_URI not found in environment variables.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
groups_collection = db["groups"]
users_collection = db["users"]

# --- FastAPI App Initialization ---
app = FastAPI()

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoint for Group Stats ---
@app.get("/api/stats/{group_id}")
async def get_group_stats(group_id: int):
    try:
        group_data = groups_collection.find_one({"_id": group_id})

        if not group_data:
            raise HTTPException(status_code=404, detail="Group ID not found")

        all_player_ids_str = group_data.get("all_players", [])
        if not all_player_ids_str:
            return {
                "groupName": group_data.get("title", f"Group {group_id}"),
                "totalGames": group_data.get("total_games", 0),
                "highestScore": 0, "uniquePlayers": 0, "topPlayers": [],
                "gameHistory": group_data.get("game_history", [])
            }

        all_player_ids_int = [int(pid) for pid in all_player_ids_str]
        player_docs_cursor = users_collection.find({"_id": {"$in": all_player_ids_int}})
        
        players_map = {doc["_id"]: doc for doc in player_docs_cursor}
        top_players, highest_total_score = [], 0

        for player_id, player_data in players_map.items():
            total_score = player_data.get("total_score", 0)
            if total_score > highest_total_score:
                highest_total_score = total_score
            top_players.append({
                # --- FIX: Prioritize first_name, but fallback to username ---
                "name": player_data.get("first_name") or player_data.get("username") or f"Player {player_id}",
                "username": player_data.get("username"),
                "score": total_score,
                "truths": player_data.get("total_truths", 0),
                "dares": player_data.get("total_dares", 0),
            })
        
        top_players.sort(key=lambda p: p["score"], reverse=True)

        return {
            "groupName": group_data.get("title", f"Group {group_id}"),
            "totalGames": group_data.get("total_games", 0),
            "highestScore": highest_total_score,
            "uniquePlayers": len(all_player_ids_int),
            "topPlayers": top_players[:10],
            "gameHistory": group_data.get("game_history", [])
        }

    except Exception as e:
        print(f"Error fetching stats for group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")

# --- API Endpoint for User Stats ---
@app.get("/api/user/{user_id}")
async def get_user_stats(user_id: int):
    try:
        user_data = users_collection.find_one({"_id": user_id})

        if not user_data:
            raise HTTPException(status_code=404, detail="User ID not found")

        groups_played_ids = user_data.get("groups_played", [])
        groups_info = []
        if groups_played_ids:
            groups_cursor = groups_collection.find({"_id": {"$in": groups_played_ids}}, {"title": 1})
            for doc in groups_cursor:
                group_id = doc["_id"]
                group_name = doc.get("title", f"Group {group_id}")
                groups_info.append({"id": group_id, "name": group_name})

        return {
            # --- FIX: Prioritize first_name, but fallback to username ---
            "name": user_data.get("first_name") or user_data.get("username") or f"User {user_id}",
            "username": user_data.get("username"),
            "stats": {
                "games_played": user_data.get("games_played", 0),
                "total_score": user_data.get("total_score", 0),
                "highest_score": user_data.get("highest_score", 0),
                "total_truths": user_data.get("total_truths", 0),
                "total_dares": user_data.get("total_dares", 0),
                "total_skips": user_data.get("total_skips", 0),
            },
            "groups_played": groups_info
        }
    except Exception as e:
        print(f"Error fetching stats for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
