#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database utilities for HelpDesk system
Утилиты для работы с базой данных системы HelpDesk
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class HelpDeskDB:
    """Класс для работы с базой данных HelpDesk"""
    
    def __init__(self, db_path='database/helpdesk.db'):
        self.db_path = db_path
        
    def get_connection(self):
        """Получение подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # для доступа по именам колонок
        return conn
    
    def execute_query(self, query, params=None):
        """Выполнение SQL запроса"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """Выполнение UPDATE/INSERT/DELETE запроса"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount
    
    # === ПОЛЬЗОВАТЕЛИ ===
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Получение пользователя по Telegram ID"""
        query = "SELECT * FROM users WHERE telegram_id = ? AND is_active = 1"
        result = self.execute_query(query, (telegram_id,))
        return dict(result[0]) if result else None
    
    def create_user(self, telegram_id: int, username: str, role: str) -> int:
        """Создание нового пользователя"""
        query = """
            INSERT INTO users (telegram_id, username, role) 
            VALUES (?, ?, ?)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (telegram_id, username, role))
            conn.commit()
            return cursor.lastrowid
    
    # === ФИЛИАЛЫ ===
    
    def get_branches(self, active_only=True) -> List[Dict]:
        """Получение списка филиалов"""
        query = "SELECT * FROM branches"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY name"
        
        result = self.execute_query(query)
        return [dict(row) for row in result]
    
    def get_branch_by_code(self, code: str) -> Optional[Dict]:
        """Получение филиала по коду"""
        query = "SELECT * FROM branches WHERE code = ? AND is_active = 1"
        result = self.execute_query(query, (code,))
        return dict(result[0]) if result else None
    
    # === КАРТРИДЖИ ===
    
    def get_cartridge_types(self) -> List[Dict]:
        """Получение типов картриджей"""
        query = "SELECT * FROM cartridge_types ORDER BY name"
        result = self.execute_query(query)
        return [dict(row) for row in result]
    
    def get_stock_by_branch(self, branch_id: int) -> List[Dict]:
        """Получение остатков картриджей по филиалу"""
        query = """
            SELECT si.*, ct.sku, ct.name as cartridge_name, b.name as branch_name
            FROM stock_items si
            JOIN cartridge_types ct ON si.cartridge_type_id = ct.id
            JOIN branches b ON si.branch_id = b.id
            WHERE si.branch_id = ?
            ORDER BY ct.name
        """
        result = self.execute_query(query, (branch_id,))
        return [dict(row) for row in result]
    
    def update_stock(self, branch_id: int, cartridge_type_id: int, quantity: int):
        """Обновление остатков на складе"""
        query = """
            INSERT OR REPLACE INTO stock_items (branch_id, cartridge_type_id, quantity)
            VALUES (?, ?, ?)
        """
        return self.execute_update(query, (branch_id, cartridge_type_id, quantity))
    
    # === ЗАЯВКИ ===
    
    def create_request(self, branch_id: int, user_id: int, priority: str, comment: str = None) -> str:
        """Создание новой заявки"""
        # Генерация уникального кода заявки
        request_code = self._generate_request_code()
        
        query = """
            INSERT INTO requests (request_code, branch_id, user_id, priority, comment)
            VALUES (?, ?, ?, ?, ?)
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (request_code, branch_id, user_id, priority, comment))
            request_id = cursor.lastrowid
            
            # Лог создания заявки
            self._log_request_action(cursor, request_id, user_id, 'created', None, 'new', 'Заявка создана')
            
            conn.commit()
            return request_code
    
    def get_request_by_code(self, request_code: str) -> Optional[Dict]:
        """Получение заявки по коду"""
        query = """
            SELECT r.*, b.name as branch_name, u.username as user_name,
                   e.username as executor_name
            FROM requests r
            JOIN branches b ON r.branch_id = b.id
            JOIN users u ON r.user_id = u.id
            LEFT JOIN users e ON r.assigned_executor_id = e.id
            WHERE r.request_code = ?
        """
        result = self.execute_query(query, (request_code,))
        return dict(result[0]) if result else None
    
    def update_request_status(self, request_code: str, new_status: str, executor_id: int = None, note: str = None):
        """Обновление статуса заявки"""
        request = self.get_request_by_code(request_code)
        if not request:
            raise ValueError(f"Заявка {request_code} не найдена")
        
        old_status = request['status']
        
        query = "UPDATE requests SET status = ?"
        params = [new_status]
        
        if new_status == 'done':
            query += ", completed_at = CURRENT_TIMESTAMP"
        
        query += " WHERE request_code = ?"
        params.append(request_code)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            # Лог изменения статуса
            user_id = executor_id or request['user_id']
            self._log_request_action(cursor, request['id'], user_id, 'status_changed', old_status, new_status, note)
            
            conn.commit()
    
    def add_request_item(self, request_code: str, cartridge_type_id: int, quantity: int):
        """Добавление позиции в заявку"""
        request = self.get_request_by_code(request_code)
        if not request:
            raise ValueError(f"Заявка {request_code} не найдена")
        
        query = """
            INSERT INTO request_items (request_id, cartridge_type_id, quantity)
            VALUES (?, ?, ?)
        """
        return self.execute_update(query, (request['id'], cartridge_type_id, quantity))
    
    def get_request_items(self, request_code: str) -> List[Dict]:
        """Получение позиций заявки"""
        query = """
            SELECT ri.*, ct.sku, ct.name as cartridge_name
            FROM request_items ri
            JOIN cartridge_types ct ON ri.cartridge_type_id = ct.id
            JOIN requests r ON ri.request_id = r.id
            WHERE r.request_code = ?
        """
        result = self.execute_query(query, (request_code,))
        return [dict(row) for row in result]
    
    # === ОТЧЕТЫ ===
    
    def get_requests_by_branch(self, branch_id: int, status: str = None) -> List[Dict]:
        """Получение заявок по филиалу"""
        query = """
            SELECT r.*, u.username, ct_count.total_items
            FROM requests r
            JOIN users u ON r.user_id = u.id
            LEFT JOIN (
                SELECT request_id, COUNT(*) as total_items
                FROM request_items
                GROUP BY request_id
            ) ct_count ON r.id = ct_count.request_id
            WHERE r.branch_id = ?
        """
        params = [branch_id]
        
        if status:
            query += " AND r.status = ?"
            params.append(status)
        
        query += " ORDER BY r.created_at DESC"
        
        result = self.execute_query(query, params)
        return [dict(row) for row in result]
    
    def get_sla_violations(self, hours_threshold: int = 1) -> List[Dict]:
        """Получение заявок с нарушением SLA"""
        query = """
            SELECT r.*, b.name as branch_name, u.username
            FROM requests r
            JOIN branches b ON r.branch_id = b.id
            JOIN users u ON r.user_id = u.id
            WHERE r.status IN ('new', 'in_progress')
            AND datetime(r.created_at, '+{} hours') < datetime('now')
            AND r.sla_notified_at IS NULL
            ORDER BY r.created_at
        """.format(hours_threshold)
        
        result = self.execute_query(query)
        return [dict(row) for row in result]
    
    def mark_sla_notified(self, request_code: str):
        """Отметка об уведомлении SLA"""
        query = "UPDATE requests SET sla_notified_at = CURRENT_TIMESTAMP WHERE request_code = ?"
        return self.execute_update(query, (request_code,))
    
    # === СЛУЖЕБНЫЕ МЕТОДЫ ===
    
    def _generate_request_code(self) -> str:
        """Генерация уникального кода заявки"""
        import random
        import string
        
        # Формат: REQ-YYYYMMDD-XXX где XXX - случайные цифры
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.digits, k=3))
        
        request_code = f"REQ-{date_part}-{random_part}"
        
        # Проверка уникальности
        existing = self.execute_query("SELECT id FROM requests WHERE request_code = ?", (request_code,))
        if existing:
            return self._generate_request_code()  # Рекурсивный вызов
        
        return request_code
    
    def _log_request_action(self, cursor, request_id: int, user_id: int, action: str, 
                           from_status: str = None, to_status: str = None, note: str = None):
        """Логирование действий с заявкой"""
        query = """
            INSERT INTO logs (request_id, user_id, action, from_status, to_status, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (request_id, user_id, action, from_status, to_status, note))
    
    def get_stats(self) -> Dict:
        """Получение общей статистики"""
        stats = {}
        
        # Общее количество заявок
        stats['total_requests'] = self.execute_query("SELECT COUNT(*) as count FROM requests")[0]['count']
        
        # По статусам
        status_query = """
            SELECT status, COUNT(*) as count 
            FROM requests 
            GROUP BY status
        """
        status_result = self.execute_query(status_query)
        stats['by_status'] = {row['status']: row['count'] for row in status_result}
        
        # По приоритетам
        priority_query = """
            SELECT priority, COUNT(*) as count 
            FROM requests 
            GROUP BY priority
        """
        priority_result = self.execute_query(priority_query)
        stats['by_priority'] = {row['priority']: row['count'] for row in priority_result}
        
        # Активные пользователи
        stats['active_users'] = self.execute_query("SELECT COUNT(*) as count FROM users WHERE is_active = 1")[0]['count']
        
        # Активные филиалы
        stats['active_branches'] = self.execute_query("SELECT COUNT(*) as count FROM branches WHERE is_active = 1")[0]['count']
        
        return stats

# Пример использования
if __name__ == "__main__":
    db = HelpDeskDB()
    
    print("📊 Статистика системы:")
    stats = db.get_stats()
    print(f"   Заявок всего: {stats['total_requests']}")
    print(f"   Активных пользователей: {stats['active_users']}")
    print(f"   Активных филиалов: {stats['active_branches']}")
    
    print("\n📈 По статусам:")
    for status, count in stats['by_status'].items():
        print(f"   {status}: {count}")
    
    print("\n🔥 По приоритетам:")
    for priority, count in stats['by_priority'].items():
        print(f"   {priority}: {count}")