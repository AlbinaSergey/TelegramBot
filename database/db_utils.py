#!/usr/bin/env python3
"""
Database utilities for HelpDesk Ecosystem
Common database operations and connection management
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(
            os.path.dirname(__file__), '..', 'helpdesk.db'
        )
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute multiple queries with different parameters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount

class UserManager:
    """User management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by Telegram ID"""
        query = """
            SELECT * FROM users 
            WHERE telegram_id = ? AND is_active = 1
        """
        results = self.db.execute_query(query, (telegram_id,))
        return results[0] if results else None
    
    def create_user(self, telegram_id: int, username: str, role: str = 'branch_user') -> int:
        """Create a new user"""
        query = """
            INSERT INTO users (telegram_id, username, role, is_active)
            VALUES (?, ?, ?, 1)
        """
        self.db.execute_update(query, (telegram_id, username, role))
        return telegram_id
    
    def update_user_role(self, telegram_id: int, role: str) -> bool:
        """Update user role"""
        query = """
            UPDATE users SET role = ? 
            WHERE telegram_id = ? AND is_active = 1
        """
        return self.db.execute_update(query, (role, telegram_id)) > 0

class BranchManager:
    """Branch management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_all_branches(self) -> List[Dict[str, Any]]:
        """Get all active branches"""
        query = """
            SELECT * FROM branches 
            WHERE is_active = 1 
            ORDER BY name
        """
        return self.db.execute_query(query)
    
    def get_branch_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get branch by code"""
        query = """
            SELECT * FROM branches 
            WHERE code = ? AND is_active = 1
        """
        results = self.db.execute_query(query, (code,))
        return results[0] if results else None

class CartridgeManager:
    """Cartridge management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_all_cartridge_types(self) -> List[Dict[str, Any]]:
        """Get all cartridge types"""
        query = """
            SELECT * FROM cartridge_types 
            ORDER BY name
        """
        return self.db.execute_query(query)
    
    def get_cartridge_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get cartridge by SKU"""
        query = """
            SELECT * FROM cartridge_types 
            WHERE sku = ?
        """
        results = self.db.execute_query(query, (sku,))
        return results[0] if results else None
    
    def get_stock_by_branch(self, branch_id: int) -> List[Dict[str, Any]]:
        """Get stock items for a specific branch"""
        query = """
            SELECT 
                si.id,
                si.quantity,
                ct.sku,
                ct.name as cartridge_name,
                b.code as branch_code,
                b.name as branch_name
            FROM stock_items si
            JOIN cartridge_types ct ON si.cartridge_type_id = ct.id
            JOIN branches b ON si.branch_id = b.id
            WHERE si.branch_id = ?
            ORDER BY ct.name
        """
        return self.db.execute_query(query, (branch_id,))

class RequestManager:
    """Request management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_request(self, request_code: str, branch_id: int, user_id: int, 
                      priority: str, comment: str = None) -> int:
        """Create a new request"""
        query = """
            INSERT INTO requests (request_code, branch_id, user_id, priority, comment)
            VALUES (?, ?, ?, ?, ?)
        """
        self.db.execute_update(query, (request_code, branch_id, user_id, priority, comment))
        
        # Get the created request ID
        query_id = "SELECT last_insert_rowid() as id"
        result = self.db.execute_query(query_id)
        return result[0]['id']
    
    def add_request_items(self, request_id: int, items: List[Tuple[int, int]]) -> bool:
        """Add items to a request (cartridge_type_id, quantity)"""
        query = """
            INSERT INTO request_items (request_id, cartridge_type_id, quantity)
            VALUES (?, ?, ?)
        """
        params = [(request_id, cartridge_type_id, quantity) for cartridge_type_id, quantity in items]
        return self.db.execute_many(query, params) > 0
    
    def get_request_by_code(self, request_code: str) -> Optional[Dict[str, Any]]:
        """Get request by code with full details"""
        query = """
            SELECT 
                r.*,
                u.username as user_name,
                u.telegram_id as user_telegram_id,
                b.code as branch_code,
                b.name as branch_name,
                ae.username as executor_name
            FROM requests r
            JOIN users u ON r.user_id = u.id
            JOIN branches b ON r.branch_id = b.id
            LEFT JOIN users ae ON r.assigned_executor_id = ae.id
            WHERE r.request_code = ?
        """
        results = self.db.execute_query(query, (request_code,))
        return results[0] if results else None
    
    def get_request_items(self, request_id: int) -> List[Dict[str, Any]]:
        """Get items for a specific request"""
        query = """
            SELECT 
                ri.*,
                ct.sku,
                ct.name as cartridge_name
            FROM request_items ri
            JOIN cartridge_types ct ON ri.cartridge_type_id = ct.id
            WHERE ri.request_id = ?
        """
        return self.db.execute_query(query, (request_id,))
    
    def update_request_status(self, request_id: int, new_status: str, 
                            user_id: int = None, note: str = None) -> bool:
        """Update request status and log the change"""
        # Get current status
        current = self.db.execute_query(
            "SELECT status FROM requests WHERE id = ?", (request_id,)
        )
        if not current:
            return False
        
        current_status = current[0]['status']
        
        # Update status
        update_query = """
            UPDATE requests SET status = ?
            WHERE id = ?
        """
        self.db.execute_update(update_query, (new_status, request_id))
        
        # Log the change
        log_query = """
            INSERT INTO logs (request_id, user_id, action, from_status, to_status, note)
            VALUES (?, ?, 'status_changed', ?, ?, ?)
        """
        self.db.execute_update(log_query, (request_id, user_id, current_status, new_status, note))
        
        return True
    
    def get_user_requests(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent requests for a user"""
        query = """
            SELECT 
                r.*,
                b.code as branch_code,
                b.name as branch_name
            FROM requests r
            JOIN branches b ON r.branch_id = b.id
            WHERE r.user_id = ?
            ORDER BY r.created_at DESC
            LIMIT ?
        """
        return self.db.execute_query(query, (user_id, limit))

class LogManager:
    """Log management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_log(self, request_id: int, user_id: int, action: str, 
                from_status: str = None, to_status: str = None, note: str = None) -> bool:
        """Add a log entry"""
        query = """
            INSERT INTO logs (request_id, user_id, action, from_status, to_status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.db.execute_update(query, (request_id, user_id, action, from_status, to_status, note)) > 0
    
    def get_request_logs(self, request_id: int) -> List[Dict[str, Any]]:
        """Get all logs for a request"""
        query = """
            SELECT 
                l.*,
                u.username as user_name
            FROM logs l
            LEFT JOIN users u ON l.user_id = u.id
            WHERE l.request_id = ?
            ORDER BY l.timestamp DESC
        """
        return self.db.execute_query(query, (request_id,))

# Utility functions
def generate_request_code() -> str:
    """Generate unique request code"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    import random
    random_suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    return f"REQ-{timestamp}-{random_suffix}"

def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str

# Initialize global database manager
db_manager = DatabaseManager()
user_manager = UserManager(db_manager)
branch_manager = BranchManager(db_manager)
cartridge_manager = CartridgeManager(db_manager)
request_manager = RequestManager(db_manager)
log_manager = LogManager(db_manager)