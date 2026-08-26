from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "dataset"
MODEL_DIR = BASE_DIR / "saved_models"
REPORT_DIR = BASE_DIR / "reports"
DB_PATH = BASE_DIR / "attrition.db"

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MINUTES", "480"))

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@hr.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

for path in (DATASET_DIR, MODEL_DIR, REPORT_DIR):
    path.mkdir(parents=True, exist_ok=True)
