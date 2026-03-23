import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INTEGRATION_CODE = PROJECT_ROOT / "integration" / "code"

if str(INTEGRATION_CODE) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_CODE))
