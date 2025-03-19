import os

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_PATH = "consortium.db"
    DATA_DIR = "data"