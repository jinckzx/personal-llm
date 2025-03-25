import sqlite3
import threading
from datetime import datetime
from typing import Optional

class SynthesisDatabaseHandler:
    def __init__(self, db_path: str = 'synthesized.db'):
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
        """Initialize database schema for synthesis results"""
        try:
            conn = self._get_connection()
            conn.execute('''
                CREATE TABLE IF NOT EXISTS synthesis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    iteration INTEGER,
                    prompt TEXT,
                    arbiter_model TEXT,
                    synthesized_text TEXT,
                    confidence REAL,
                    analysis TEXT,
                    dissenting_views TEXT
                )''')
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Synthesis database initialization failed: {str(e)}")

    def log_synthesis(self, iteration: int, prompt: str, arbiter: str, 
                     synthesized_text: str, confidence: float, 
                     analysis: str, dissent: str):
        """Log synthesis results to the database"""
        try:
            conn = self._get_connection()
            conn.execute('''
                INSERT INTO synthesis_results 
                (timestamp, iteration, prompt, arbiter_model, 
                 synthesized_text, confidence, analysis, dissenting_views)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    datetime.now(),
                    iteration,
                    prompt,
                    arbiter,
                    synthesized_text,
                    confidence,
                    analysis,
                    dissent
                )
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to log synthesis: {str(e)}")

    def close(self):
        """Close the database connection"""
        if hasattr(self.thread_local, "conn"):
            self.thread_local.conn.close()
            del self.thread_local.conn