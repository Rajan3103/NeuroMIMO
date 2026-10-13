"""SQLite database storage for simulation and training experiment history."""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import os

DB_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DB_PATH = os.path.join(DB_DIR, "experiments.db")


def init_db(db_path: str = DB_PATH) -> None:
    """Initializes SQLite database tables if they do not exist."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                name TEXT NOT NULL,
                config TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                snr_db REAL NOT NULL,
                nmse REAL NOT NULL,
                ber REAL NOT NULL,
                ser REAL NOT NULL,
                execution_time_ms REAL NOT NULL,
                results TEXT,
                notes TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS training_runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                epochs INTEGER NOT NULL,
                final_train_loss REAL NOT NULL,
                final_val_loss REAL NOT NULL,
                checkpoint_path TEXT NOT NULL,
                history TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_experiment(
    exp_id: str,
    name: str,
    config: Dict[str, Any],
    algorithm: str,
    snr_db: float,
    nmse: float,
    ber: float,
    ser: float,
    execution_time_ms: float,
    results: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
    db_path: str = DB_PATH,
) -> None:
    """Inserts or updates an experiment run result in the SQLite database."""
    init_db(db_path)
    created_at = datetime.now(timezone.utc).isoformat()
    config_json = json.dumps(config)
    results_json = json.dumps(results or {})
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO experiments (
                id, created_at, name, config, algorithm, snr_db, nmse, ber, ser, execution_time_ms, results, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp_id,
                created_at,
                name,
                config_json,
                algorithm,
                snr_db,
                nmse,
                ber,
                ser,
                execution_time_ms,
                results_json,
                notes or "",
            ),
        )
        conn.commit()


def get_all_experiments(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Retrieves list of all saved simulation experiments."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            try:
                d["config"] = json.loads(d["config"])
            except Exception:
                pass
            if d.get("results"):
                try:
                    d["results"] = json.loads(d["results"])
                except Exception:
                    pass
            result.append(d)
        return result


def get_experiment_by_id(exp_id: str, db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves a single simulation experiment by its unique ID."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE id = ?", (exp_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["config"] = json.loads(d["config"])
        except Exception:
            pass
        if d.get("results"):
            try:
                d["results"] = json.loads(d["results"])
            except Exception:
                pass
        return d


def save_training_run(
    run_id: str,
    epochs: int,
    final_train_loss: float,
    final_val_loss: float,
    checkpoint_path: str,
    history: List[Dict[str, Any]],
    db_path: str = DB_PATH,
) -> None:
    """Inserts a DNN model training run into the database."""
    init_db(db_path)
    created_at = datetime.now(timezone.utc).isoformat()
    history_json = json.dumps(history)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO training_runs (
                id, created_at, epochs, final_train_loss, final_val_loss, checkpoint_path, history
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                created_at,
                epochs,
                final_train_loss,
                final_val_loss,
                checkpoint_path,
                history_json,
            ),
        )
        conn.commit()


def get_latest_training_run(db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieves the most recent training run."""
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM training_runs ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        try:
            d["history"] = json.loads(d["history"])
        except Exception:
            pass
        return d
