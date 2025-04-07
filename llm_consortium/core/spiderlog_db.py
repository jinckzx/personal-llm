# spiderlog_db.py
import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd

class SpiderDatasetLogger:
    def __init__(self, db_path: str = 'spiderdatasetqueries.db'):
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
        """Initialize database schema for spider dataset logging"""
        try:
            conn = self._get_connection()
            conn.execute('''
                CREATE TABLE IF NOT EXISTS spider_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    db_schema TEXT,
                    natural_language_query TEXT,
                    intent_category TEXT,
                    generated_sql TEXT,
                    confidence REAL,
                    model_responses TEXT  -- JSON array of all model responses
                )''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_intent_category 
                ON spider_queries(intent_category)
            ''')
            conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Spider dataset DB initialization failed: {str(e)}")

    def log_query(
        self,
        db_schema: str,
        natural_language_query: str,
        intent_category: str,
        generated_sql: str,
        confidence: float,
        model_responses: List[Dict]
    ):
        """Log a complete spider dataset query with intent classification"""
        try:
            conn = self._get_connection()
            conn.execute('''
                INSERT INTO spider_queries 
                (timestamp, db_schema, natural_language_query, 
                 intent_category, generated_sql, confidence, model_responses)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    datetime.now(),
                    db_schema,
                    natural_language_query,
                    intent_category,
                    generated_sql,
                    confidence,
                    str(model_responses)  # Serialize as JSON string
                )
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise RuntimeError(f"Failed to log spider query: {str(e)}")

    def get_queries_by_intent(self, intent_category: str) -> pd.DataFrame:
        """Retrieve queries filtered by intent category"""
        try:
            conn = self._get_connection()
            df = pd.read_sql(
                '''SELECT * FROM spider_queries 
                   WHERE intent_category = ? 
                   ORDER BY timestamp DESC''',
                conn,
                params=(intent_category,)
            )
            return df
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to fetch queries by intent: {str(e)}")

    def close(self):
        """Close the database connection"""
        if hasattr(self.thread_local, "conn"):
            self.thread_local.conn.close()
            del self.thread_local.conn