#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed data script for HelpDesk system
Создание начальных данных для тестирования системы
"""

import sqlite3
import hashlib
from datetime import datetime

def create_password_hash(password):
    """Создание хеша пароля для пользователей"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database(db_path='database/helpdesk.db'):
    """Заполнение базы данных начальными данными"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Создание структуры БД из schema.sql
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
            cursor.executescript(schema)
        
        # Заполнение филиалов
        branches_data = [
            ('F-KAZ', 'Филиал Казань', 'Казань'),
            ('F-MSK', 'Филиал Москва', 'Москва'),
            ('F-SPB', 'Филиал Санкт-Петербург', 'Санкт-Петербург'),
            ('ГОРОД-12', 'Отделение №12', 'Нижний Новгород'),
            ('ГОРОД-45', 'Отделение №45', 'Екатеринбург'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO branches (code, name, city) VALUES (?, ?, ?)",
            branches_data
        )
        
        # Заполнение типов картриджей
        cartridge_types_data = [
            ('HP-CF248A', 'HP 48A LaserJet Pro'),
            ('HP-CE285A', 'HP 85A LaserJet Pro'),
            ('CANON-728', 'Canon 728 MF4410/4430'),
            ('CANON-725', 'Canon 725 LBP6000/6020'),
            ('XEROX-3020', 'Xerox WorkCentre 3020'),
            ('BROTHER-TN2090', 'Brother TN-2090'),
            ('SAMSUNG-MLT-D111S', 'Samsung MLT-D111S'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO cartridge_types (sku, name) VALUES (?, ?)",
            cartridge_types_data
        )
        
        # Заполнение пользователей
        users_data = [
            (12345678, 'admin_user', 'admin', create_password_hash('admin123')),
            (87654321, 'executor1', 'executor', create_password_hash('exec123')),
            (11111111, 'branch_user1', 'branch_user', None),
            (22222222, 'branch_user2', 'branch_user', None),
            (33333333, 'executor2', 'executor', create_password_hash('exec456')),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO users (telegram_id, username, role, password_hash) VALUES (?, ?, ?, ?)",
            users_data
        )
        
        # Заполнение остатков на складе (случайные данные)
        import random
        
        # Получаем ID филиалов и картриджей
        cursor.execute("SELECT id FROM branches")
        branch_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM cartridge_types")
        cartridge_ids = [row[0] for row in cursor.fetchall()]
        
        # Создаем остатки для каждого филиала и типа картриджа
        stock_data = []
        for branch_id in branch_ids:
            for cartridge_id in cartridge_ids:
                quantity = random.randint(0, 50)  # случайное количество от 0 до 50
                stock_data.append((branch_id, cartridge_id, quantity))
        
        cursor.executemany(
            "INSERT OR IGNORE INTO stock_items (branch_id, cartridge_type_id, quantity) VALUES (?, ?, ?)",
            stock_data
        )
        
        # Создание тестовых заявок
        cursor.execute("SELECT id FROM users WHERE role = 'branch_user'")
        branch_user_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM users WHERE role = 'executor'")
        executor_ids = [row[0] for row in cursor.fetchall()]
        
        test_requests = [
            ('REQ-001', branch_ids[0], branch_user_ids[0], 'high', 'new', 'Срочно нужны картриджи для принтера в офисе'),
            ('REQ-002', branch_ids[1], branch_user_ids[0], 'normal', 'in_progress', 'Заказ картриджей на следующую неделю'),
            ('REQ-003', branch_ids[2], branch_user_ids[1] if len(branch_user_ids) > 1 else branch_user_ids[0], 'low', 'done', 'Плановая заявка на картриджи'),
        ]
        
        for i, req_data in enumerate(test_requests):
            cursor.execute(
                """INSERT OR IGNORE INTO requests 
                   (request_code, branch_id, user_id, priority, status, comment, assigned_executor_id) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (*req_data, executor_ids[0] if i < 2 else None)
            )
        
        # Элементы заявок
        cursor.execute("SELECT id FROM requests")
        request_ids = [row[0] for row in cursor.fetchall()]
        
        request_items_data = [
            (request_ids[0], cartridge_ids[0], 2),  # 2 HP-CF248A
            (request_ids[0], cartridge_ids[2], 1),  # 1 CANON-728
            (request_ids[1], cartridge_ids[1], 3),  # 3 HP-CE285A
            (request_ids[2], cartridge_ids[4], 1),  # 1 XEROX-3020
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO request_items (request_id, cartridge_type_id, quantity) VALUES (?, ?, ?)",
            request_items_data
        )
        
        # Логи изменений
        logs_data = [
            (request_ids[0], branch_user_ids[0], 'created', None, 'new', 'Заявка создана'),
            (request_ids[1], branch_user_ids[0], 'created', None, 'new', 'Заявка создана'),
            (request_ids[1], executor_ids[0], 'status_changed', 'new', 'in_progress', 'Заявка взята в работу'),
            (request_ids[2], branch_user_ids[1] if len(branch_user_ids) > 1 else branch_user_ids[0], 'created', None, 'new', 'Заявка создана'),
            (request_ids[2], executor_ids[0], 'status_changed', 'new', 'in_progress', 'Заявка взята в работу'),
            (request_ids[2], executor_ids[0], 'status_changed', 'in_progress', 'done', 'Заявка выполнена'),
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO logs 
               (request_id, user_id, action, from_status, to_status, note) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            logs_data
        )
        
        conn.commit()
        print("✅ База данных успешно заполнена начальными данными!")
        print(f"📊 Создано:")
        print(f"   - Филиалов: {len(branches_data)}")
        print(f"   - Типов картриджей: {len(cartridge_types_data)}")
        print(f"   - Пользователей: {len(users_data)}")
        print(f"   - Остатков на складе: {len(stock_data)}")
        print(f"   - Тестовых заявок: {len(test_requests)}")
        
    except Exception as e:
        print(f"❌ Ошибка при заполнении БД: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()