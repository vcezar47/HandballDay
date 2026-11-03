import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "handballday")
PORT = int(os.getenv("PORT", "3000"))

# Origins allowed to call the API directly (the Vite dev server also proxies /api).
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
