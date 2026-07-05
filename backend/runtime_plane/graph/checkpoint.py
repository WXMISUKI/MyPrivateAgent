"""
Checkpoint Store - 执行状态检查点存储

对标 LangGraph 的 MemorySaver / SqliteSaver / PostgresSaver。
支持保存、加载、列举检查点，用于中断恢复和执行回放。
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Checkpoint data
# ---------------------------------------------------------------------------

@dataclass
class Checkpoint:
    """检查点快照。"""
    thread_id: str
    step: int
    state: dict[str, Any]
    current_node: str
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_checkpoint_id: str | None = None

    @property
    def checkpoint_id(self) -> str:
        return f"{self.thread_id}:step:{self.step}"

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "thread_id": self.thread_id,
            "step": self.step,
            "state": self.state,
            "current_node": self.current_node,
            "metadata": self.metadata,
            "parent_checkpoint_id": self.parent_checkpoint_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        return cls(
            thread_id=data["thread_id"],
            step=data["step"],
            state=data["state"],
            current_node=data["current_node"],
            metadata=data.get("metadata", {}),
            parent_checkpoint_id=data.get("parent_checkpoint_id"),
        )


# ---------------------------------------------------------------------------
# Store protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class CheckpointStore(Protocol):
    """检查点存储协议。"""

    def save(self, thread_id: str, checkpoint: Checkpoint) -> None:
        """保存检查点。"""
        ...

    def load(self, thread_id: str, checkpoint_id: str | None = None) -> Checkpoint | None:
        """加载检查点。checkpoint_id 为 None 时加载最新。"""
        ...

    def list_checkpoints(self, thread_id: str) -> list[Checkpoint]:
        """列出指定线程的所有检查点。"""
        ...

    def delete(self, thread_id: str) -> None:
        """删除指定线程的所有检查点。"""
        ...


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

class InMemoryCheckpointStore:
    """内存检查点存储，用于开发和测试。"""

    def __init__(self):
        self._store: dict[str, list[Checkpoint]] = {}

    def save(self, thread_id: str, checkpoint: Checkpoint) -> None:
        if thread_id not in self._store:
            self._store[thread_id] = []
        self._store[thread_id].append(checkpoint)

    def load(self, thread_id: str, checkpoint_id: str | None = None) -> Checkpoint | None:
        checkpoints = self._store.get(thread_id, [])
        if not checkpoints:
            return None
        if checkpoint_id:
            for cp in checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    return cp
            return None
        return checkpoints[-1]  # 最新

    def list_checkpoints(self, thread_id: str) -> list[Checkpoint]:
        return list(self._store.get(thread_id, []))

    def delete(self, thread_id: str) -> None:
        self._store.pop(thread_id, None)


# ---------------------------------------------------------------------------
# SQLite store
# ---------------------------------------------------------------------------

class SQLiteCheckpointStore:
    """SQLite 检查点存储，用于本地持久化。"""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_table()

    def _init_table(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                step INTEGER NOT NULL,
                state TEXT NOT NULL,
                current_node TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                parent_checkpoint_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_checkpoints_thread
            ON checkpoints(thread_id, step)
        """)
        self._conn.commit()

    def save(self, thread_id: str, checkpoint: Checkpoint) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO checkpoints (checkpoint_id, thread_id, step, state, current_node, metadata, parent_checkpoint_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                checkpoint.checkpoint_id,
                thread_id,
                checkpoint.step,
                json.dumps(checkpoint.state, ensure_ascii=False, default=str),
                checkpoint.current_node,
                json.dumps(checkpoint.metadata, ensure_ascii=False),
                checkpoint.parent_checkpoint_id,
            ),
        )
        self._conn.commit()

    def load(self, thread_id: str, checkpoint_id: str | None = None) -> Checkpoint | None:
        if checkpoint_id:
            row = self._conn.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?",
                (checkpoint_id,),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT * FROM checkpoints WHERE thread_id = ? ORDER BY step DESC LIMIT 1",
                (thread_id,),
            ).fetchone()

        if not row:
            return None

        return Checkpoint(
            thread_id=row["thread_id"],
            step=row["step"],
            state=json.loads(row["state"]),
            current_node=row["current_node"],
            metadata=json.loads(row["metadata"]),
            parent_checkpoint_id=row["parent_checkpoint_id"],
        )

    def list_checkpoints(self, thread_id: str) -> list[Checkpoint]:
        rows = self._conn.execute(
            "SELECT * FROM checkpoints WHERE thread_id = ? ORDER BY step",
            (thread_id,),
        ).fetchall()
        return [
            Checkpoint(
                thread_id=r["thread_id"],
                step=r["step"],
                state=json.loads(r["state"]),
                current_node=r["current_node"],
                metadata=json.loads(r["metadata"]),
                parent_checkpoint_id=r["parent_checkpoint_id"],
            )
            for r in rows
        ]

    def delete(self, thread_id: str) -> None:
        self._conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        self._conn.commit()

    def close(self):
        self._conn.close()
