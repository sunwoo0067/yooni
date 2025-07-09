"""Base worker class for multi-account, multi-market automation system."""
from __future__ import annotations

import sys
import pathlib
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

# Ensure project root is on sys.path
project_root = pathlib.Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from market.coupaing.utils.supabase_client import get_supabase_client


class BaseWorkerV2(ABC):
    """Base class for all automation workers with multi-account support."""

    def __init__(self, user_id: str, market_account_id: int = None, supplier_account_id: int = None):
        self.user_id = user_id
        self.market_account_id = market_account_id
        self.supplier_account_id = supplier_account_id
        self.supabase = get_supabase_client()
        
        # Load account information
        self.market_account = None
        self.supplier_account = None
        
        if market_account_id:
            self.market_account = self._load_market_account()
        if supplier_account_id:
            self.supplier_account = self._load_supplier_account()

    def _load_market_account(self) -> Dict[str, Any]:
        """Load market account information including credentials."""
        response = (
            self.supabase.table("market_accounts")
            .select("*, markets(*)")
            .eq("id", self.market_account_id)
            .eq("user_id", self.user_id)
            .single()
            .execute()
        )
        
        if not response.data:
            raise ValueError(f"Market account {self.market_account_id} not found for user {self.user_id}")
        
        return response.data

    def _load_supplier_account(self) -> Dict[str, Any]:
        """Load supplier account information including credentials."""
        response = (
            self.supabase.table("supplier_accounts")
            .select("*, suppliers(*)")
            .eq("id", self.supplier_account_id)
            .eq("user_id", self.user_id)
            .single()
            .execute()
        )
        
        if not response.data:
            raise ValueError(f"Supplier account {self.supplier_account_id} not found for user {self.user_id}")
        
        return response.data

    def log(self, level: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log worker activity to automation_logs table."""
        try:
            log_data = {
                "user_id": self.user_id,
                "market_account_id": self.market_account_id,
                "supplier_account_id": self.supplier_account_id,
                "worker_type": self.__class__.__name__,
                "level": level,
                "message": message,
                "details": details or {},
            }
            
            self.supabase.table("automation_logs").insert(log_data).execute()
            
            # Also print to console
            print(f"[{level}] {message}")
            if details:
                print(f"  Details: {details}")
                
        except Exception as e:
            print(f"Failed to log: {e}")

    def update_worker_status(self, status: str, next_run_at: datetime = None):
        """Update worker status in the database."""
        try:
            update_data = {
                "status": status,
                "last_run_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            if next_run_at:
                update_data["next_run_at"] = next_run_at.isoformat()
            
            self.supabase.table("worker_status").upsert({
                "user_id": self.user_id,
                "market_account_id": self.market_account_id,
                "worker_type": self.__class__.__name__,
                **update_data
            }, on_conflict="market_account_id,worker_type").execute()
            
        except Exception as e:
            print(f"Failed to update worker status: {e}")

    @abstractmethod
    def run(self, **kwargs):
        """Run the worker task. Must be implemented by subclasses."""
        pass