from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_DIR = BASE_DIR / "ai_service" / "app" / "data"
PARSED_DIR = BASE_DIR / "datasets" / "parsed"

DATA_DIR.mkdir(parents=True, exist_ok=True)