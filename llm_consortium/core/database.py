import sqlite3
import threading
from datetime import datetime
from typing import Optional
from ..config.models import LogEntry

class DatabaseHandler:
    def __init__(self, db_path: str = 'consortium.db'):
        self.db_path = db_path
        self.thread_local = threading.local()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get or create a thread-local database connection"""
        if not hasattr(self.thread_local, "conn") or not self.thread_local.conn:
            self.thread_local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.thread_local.conn.row_factory = sqlite3.Row
        return self.thread_local.conn

    def _init_db(self):
        """Initialize database schema"""
        try:
            conn = self._get_connection()
            conn.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    prompt TEXT,
                    model TEXT,
                    response TEXT,
                    confidence REAL,
                    latency REAL,
                    iteration INTEGER
                )''')
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Database initialization failed: {str(e)}")

    def log_interaction(self, entry: LogEntry):
        """Log an interaction to the database"""
        try:
            conn = self._get_connection()
            conn.execute('''
                INSERT INTO interactions 
                (timestamp, prompt, model, response, confidence, latency, iteration)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    entry.timestamp,
                    entry.prompt,
                    entry.model,
                    entry.response,
                    entry.confidence,
                    entry.latency,
                    entry.iteration
                )
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to log interaction: {str(e)}")

    def close(self):
        """Close the database connection"""
        if hasattr(self.thread_local, "conn"):
            self.thread_local.conn.close()
            del self.thread_local.conn
            