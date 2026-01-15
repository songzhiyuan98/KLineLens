"""
Signal Evaluation Database Module

SQLite database for storing and retrieving signal evaluation records.
"""

import os
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class SignalEvaluation:
    """Signal evaluation record"""
    id: str
    ticker: str
    tf: str
    created_at: str  # ISO timestamp
    signal_type: str
    direction: str  # up / down
    predicted_behavior: str
    entry_price: float
    target_price: float
    invalidation_price: float
    confidence: float
    notes: Optional[str] = None
    status: str = "pending"  # pending / correct / incorrect
    result: Optional[str] = None  # target_hit / invalidation_hit / partial_correct / direction_wrong / timeout
    actual_outcome: Optional[str] = None
    evaluation_notes: Optional[str] = None
    evaluated_at: Optional[str] = None


@dataclass
class EvaluationStatistics:
    """Evaluation statistics"""
    total_predictions: int
    correct: int
    incorrect: int
    pending: int
    accuracy_rate: float
    by_signal_type: Dict[str, Dict[str, Any]]


class SignalEvaluationDB:
    """SQLite database for signal evaluations"""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize database connection"""
        if db_path is None:
            # Default path: apps/api/data/klinelens.db
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'klinelens.db')

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signal_evaluations (
                    id TEXT PRIMARY KEY,
                    ticker TEXT NOT NULL,
                    tf TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    predicted_behavior TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    target_price REAL NOT NULL,
                    invalidation_price REAL NOT NULL,
                    confidence REAL NOT NULL,
                    notes TEXT,
                    status TEXT DEFAULT 'pending',
                    result TEXT,
                    actual_outcome TEXT,
                    evaluation_notes TEXT,
                    evaluated_at TEXT
                )
            ''')

            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker_tf ON signal_evaluations(ticker, tf)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON signal_evaluations(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON signal_evaluations(created_at)')

            conn.commit()
        finally:
            conn.close()

    def create(self, evaluation: SignalEvaluation) -> SignalEvaluation:
        """Create a new signal evaluation record"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO signal_evaluations
                (id, ticker, tf, created_at, signal_type, direction, predicted_behavior,
                 entry_price, target_price, invalidation_price, confidence, notes, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                evaluation.id,
                evaluation.ticker,
                evaluation.tf,
                evaluation.created_at,
                evaluation.signal_type,
                evaluation.direction,
                evaluation.predicted_behavior,
                evaluation.entry_price,
                evaluation.target_price,
                evaluation.invalidation_price,
                evaluation.confidence,
                evaluation.notes,
                evaluation.status,
            ))
            conn.commit()
            return evaluation
        finally:
            conn.close()

    def get(self, eval_id: str) -> Optional[SignalEvaluation]:
        """Get a single evaluation by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM signal_evaluations WHERE id = ?', (eval_id,))
            row = cursor.fetchone()
            if row:
                return SignalEvaluation(**dict(row))
            return None
        finally:
            conn.close()

    def list(
        self,
        ticker: str,
        tf: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[SignalEvaluation]:
        """List evaluations with filters"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()

            query = 'SELECT * FROM signal_evaluations WHERE ticker = ?'
            params = [ticker]

            if tf:
                query += ' AND tf = ?'
                params.append(tf)

            if status:
                query += ' AND status = ?'
                params.append(status)

            query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [SignalEvaluation(**dict(row)) for row in rows]
        finally:
            conn.close()

    def count(
        self,
        ticker: str,
        tf: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count evaluations with filters"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            query = 'SELECT COUNT(*) FROM signal_evaluations WHERE ticker = ?'
            params = [ticker]

            if tf:
                query += ' AND tf = ?'
                params.append(tf)

            if status:
                query += ' AND status = ?'
                params.append(status)

            cursor.execute(query, params)
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def update(
        self,
        eval_id: str,
        status: str,
        result: str,
        actual_outcome: str,
        evaluation_notes: Optional[str] = None
    ) -> Optional[SignalEvaluation]:
        """Update evaluation result"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE signal_evaluations
                SET status = ?, result = ?, actual_outcome = ?, evaluation_notes = ?, evaluated_at = ?
                WHERE id = ?
            ''', (
                status,
                result,
                actual_outcome,
                evaluation_notes,
                datetime.utcnow().isoformat() + 'Z',
                eval_id,
            ))
            conn.commit()

            if cursor.rowcount == 0:
                return None

            return self.get(eval_id)
        finally:
            conn.close()

    def get_statistics(self, ticker: str, tf: Optional[str] = None) -> EvaluationStatistics:
        """Get evaluation statistics for a ticker"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()

            # Build base query
            base_where = 'WHERE ticker = ?'
            params = [ticker]
            if tf:
                base_where += ' AND tf = ?'
                params.append(tf)

            # Total counts by status
            cursor.execute(f'''
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN status = 'incorrect' THEN 1 ELSE 0 END) as incorrect,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM signal_evaluations {base_where}
            ''', params)
            row = cursor.fetchone()
            total = row[0] or 0
            correct = row[1] or 0
            incorrect = row[2] or 0
            pending = row[3] or 0

            # Accuracy rate (excluding pending)
            evaluated = correct + incorrect
            accuracy_rate = correct / evaluated if evaluated > 0 else 0.0

            # By signal type
            cursor.execute(f'''
                SELECT
                    signal_type,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'correct' THEN 1 ELSE 0 END) as correct
                FROM signal_evaluations {base_where}
                GROUP BY signal_type
            ''', params)

            by_signal_type = {}
            for row in cursor.fetchall():
                sig_type = row[0]
                sig_total = row[1]
                sig_correct = row[2]
                sig_evaluated = sig_total - (sig_total - (sig_correct + (sig_total - sig_correct if sig_correct else sig_total)))
                # Recalculate evaluated count
                cursor.execute(f'''
                    SELECT COUNT(*) FROM signal_evaluations
                    {base_where} AND signal_type = ? AND status != 'pending'
                ''', params + [sig_type])
                sig_evaluated = cursor.fetchone()[0]

                by_signal_type[sig_type] = {
                    "total": sig_total,
                    "correct": sig_correct,
                    "accuracy": sig_correct / sig_evaluated if sig_evaluated > 0 else 0.0
                }

            return EvaluationStatistics(
                total_predictions=total,
                correct=correct,
                incorrect=incorrect,
                pending=pending,
                accuracy_rate=accuracy_rate,
                by_signal_type=by_signal_type
            )
        finally:
            conn.close()

    def delete(self, eval_id: str) -> bool:
        """Delete an evaluation record"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM signal_evaluations WHERE id = ?', (eval_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()


def generate_eval_id() -> str:
    """Generate a unique evaluation ID"""
    date_str = datetime.utcnow().strftime('%Y%m%d')
    short_uuid = uuid.uuid4().hex[:6]
    return f"eval_{date_str}_{short_uuid}"
