import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
GAME_ROOT = PROJECT_ROOT / "moneypoly" / "moneypoly"

if str(GAME_ROOT) not in sys.path:
    sys.path.insert(0, str(GAME_ROOT))
