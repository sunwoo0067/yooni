"""Base class for automation workers.

Each worker processes a single `accounts` row (market account).
Child classes implement the concrete `run()` method.
"""
from __future__ import annotations

import abc
import os
from typing import Any, Dict

from dotenv import load_dotenv
from supabase import Client

# Ensure env variables are loaded (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(project_root, '.env'))

from market.coupaing.utils.supabase_client import get_supabase_client  # pylint: disable=wrong-import-position


class BaseWorker(abc.ABC):
    """Abstract base worker tied to a specific market account."""

    def __init__(self, account_id: int):
        self.account_id: int = account_id
        self.supabase: Client = get_supabase_client()
        # Load account row + market info
        data = (
            self.supabase.table('accounts')
            .select('*, markets(*)')
            .eq('id', account_id)
            .single()
            .execute()
        )
        if isinstance(data, dict) and data.get('error'):
            raise RuntimeError(f"Account fetch error: {data['error']}")
        if not getattr(data, 'data', None):
            raise ValueError(f"Account id {account_id} not found")
        self.account: Dict[str, Any] = data.data  # type: ignore
        self.market: Dict[str, Any] = self.account.get('markets')  # Joined object

    @abc.abstractmethod
    def run(self) -> None:  # pragma: no cover
        """Execute worker logic (must be overridden)."""

    # Helper: insert log
    def log(self, level: str, message: str, payload: Dict[str, Any] | None = None):
        self.supabase.table('automation_logs').insert(
            {
                'level': level,
                'message': message,
                'payload': payload or {},
            }
        ).execute()
