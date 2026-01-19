
import sqlite3
import os

class Memori:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    entity_id TEXT,
                    process_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def attribution(self, entity_id, process_id):
        self.entity_id = entity_id
        self.process_id = process_id

    def add(self, content):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memory (content, entity_id, process_id) VALUES (?, ?, ?)",
                (content, getattr(self, "entity_id", "Unknown"), getattr(self, "process_id", "Unknown"))
            )

    def search(self, query):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT content, created_at FROM memory WHERE content LIKE ? ORDER BY created_at DESC",
                (f"%{query}%",)
            )
            rows = cursor.fetchall()
            if not rows:
                return "没有找到相关记忆。"
            return "\n---\n".join([f"[{row[1]}] {row[0]}" for row in rows])
