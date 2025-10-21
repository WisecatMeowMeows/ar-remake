import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PLAYER_FILE = os.path.join(DATA_DIR, "player.json")

DEFAULT_STATS = {
    "health": 100,
    "stamina": 100,
    "charisma": 10,
    "gold": 50,
}


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_player():
    """Load player stats from disk or create default."""
    ensure_data_dir()
    if os.path.exists(PLAYER_FILE):
        try:
            with open(PLAYER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_STATS.copy()


def save_player(stats):
    """Save player stats to disk."""
    ensure_data_dir()
    with open(PLAYER_FILE, "w") as f:
        json.dump(stats, f, indent=2)


def modify_stat(stats, key, delta):
    """Modify a stat by delta, ensuring no negative values."""
    stats[key] = max(0, stats.get(key, 0) + delta)
    return stats
