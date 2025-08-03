#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed data script with real medical branches for HMAO region
Заполнение базы данных реальными филиалами и отделениями ХМАО
"""

import sqlite3
import hashlib
from datetime import datetime

def create_password_hash(password):
    """Создание хеша пароля для пользователей"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database_with_real_branches(db_path='database/helpdesk.db'):
    """Заполнение базы данных реальными филиалами ХМАО"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Создание структуры БД из schema.sql
        with open('database/schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
            cursor.executescript(schema)
        
        # Реальные филиалы и отделения ХМАО
        branches_data = [
            # Филиалы (основные территориальные подразделения)
            ('F-SUR', 'Сургутский филиал', 'Сургут'),
            ('F-NGV', 'Нижневартовский филиал', 'Нижневартовск'),
            ('F-NUR', 'Нефтеюганский филиал', 'Нефтеюганск'),
            ('F-KHM', 'Ханты-Мансийский филиал', 'Ханты-Мансийск'),
            ('F-NOY', 'Ноябрьский филиал', 'Ноябрьск'),
            ('F-NYA', 'Нягань филиал', 'Нягань'),
            ('F-LAN', 'Лангепас филиал', 'Лангепас'),
            ('F-MEG', 'Мегион филиал', 'Мегион'),
            ('F-RAD', 'Радужный филиал', 'Радужный'),
            ('F-POK', 'Покачи филиал', 'Покачи'),
            
            # Отделения в крупных городах
            ('OTD-SUR-01', 'Сургут отделение №1', 'Сургут'),
            ('OTD-SUR-02', 'Сургут отделение №2', 'Сургут'),
            ('OTD-SUR-03', 'Сургут отделение №3', 'Сургут'),
            ('OTD-SUR-04', 'Сургут отделение №4', 'Сургут'),
            ('OTD-NGV-01', 'Нижневартовск отделение №1', 'Нижневартовск'),
            ('OTD-NGV-02', 'Нижневартовск отделение №2', 'Нижневартовск'),
            ('OTD-NGV-03', 'Нижневартовск отделение №3', 'Нижневартовск'),
            ('OTD-NUR-01', 'Нефтеюганск отделение №1', 'Нефтеюганск'),
            ('OTD-NUR-02', 'Нефтеюганск отделение №2', 'Нефтеюганск'),
            
            # Корпус аппарата управления и отделения в нем
            ('АУ-ЦЕНТР', 'Центральный аппарат управления', 'Ханты-Мансийск'),
            ('АУ-АДМ', 'Административный корпус', 'Ханты-Мансийск'),
            ('АУ-ИТ', 'IT отдел аппарата управления', 'Ханты-Мансийск'),
            ('АУ-ФИН', 'Финансовый отдел', 'Ханты-Мансийск'),
            ('АУ-КАД', 'Кадровая служба', 'Ханты-Мансийск'),
            ('АУ-ЮР', 'Юридический отдел', 'Ханты-Мансийск'),
            ('АУ-БУХ', 'Бухгалтерия', 'Ханты-Мансийск'),
            ('АУ-МТО', 'Материально-техническое обеспечение', 'Ханты-Мансийск'),
            
            # Дополнительные районные отделения
            ('OTD-SVER', 'Северное отделение', 'Советский'),
            ('OTD-BELY', 'Белоярский центр', 'Белоярский'),
            ('OTD-OKTY', 'Октябрьское отделение', 'Октябрьское'),
            ('OTD-KOND', 'Кондинское отделение', 'Урай'),
            ('OTD-KOGAL', 'Когалымское отделение', 'Когалым'),
            ('OTD-YUGOR', 'Югорское отделение', 'Югорск'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO branches (code, name, city) VALUES (?, ?, ?)",
            branches_data
        )
        
        # Типы картриджей (современные модели для медицинского оборудования)
        cartridge_types_data = [
            ('HP-CF248A', 'HP 48A LaserJet Pro M15/M28/M29'),
            ('HP-CE285A', 'HP 85A LaserJet Pro P1102/M1132/M1212'),
            ('HP-CF283A', 'HP 83A LaserJet Pro MFP M125/M127/M201/M225'),
            ('CANON-728', 'Canon 728 MF4410/4430/4450/4550/4570/4580'),
            ('CANON-725', 'Canon 725 LBP6000/6020/6020B/MF3010'),
            ('CANON-712', 'Canon 712 LBP3010/3100'),
            ('XEROX-3020', 'Xerox WorkCentre 3020/3025'),
            ('XEROX-3052', 'Xerox WorkCentre 3052/3260'),
            ('BROTHER-TN2090', 'Brother TN-2090 HL-2132/DCP-7057'),
            ('BROTHER-TN2275', 'Brother TN-2275 HL-2240/2250'),
            ('SAMSUNG-MLT-D111S', 'Samsung MLT-D111S Xpress M2020/M2070'),
            ('SAMSUNG-MLT-D101S', 'Samsung MLT-D101S ML-2160/2165/SCX-3400'),
            ('KYOCERA-TK1110', 'Kyocera TK-1110 FS-1040/1020/1120'),
            ('OKI-44574705', 'OKI 44574705 B411/B431/MB461/MB471'),
            ('RICOH-SP311', 'Ricoh SP 311HS Aficio SP 311/325'),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO cartridge_types (sku, name) VALUES (?, ?)",
            cartridge_types_data
        )
        
        # Пользователи системы
        users_data = [
            (100000001, 'admin_system', 'admin', create_password_hash('admin123secure')),
            (200000001, 'executor_main', 'executor', create_password_hash('exec123secure')),
            (300000001, 'branch_surgut', 'branch_user', None),
            (300000002, 'branch_ngv', 'branch_user', None),
            (300000003, 'branch_nef', 'branch_user', None),
            (300000004, 'branch_hmao', 'branch_user', None),
            (200000002, 'executor_senior', 'executor', create_password_hash('exec456secure')),
            (200000003, 'executor_it', 'executor', create_password_hash('exec789secure')),
            (100000002, 'admin_regional', 'admin', create_password_hash('admin456secure')),
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO users (telegram_id, username, role, password_hash) VALUES (?, ?, ?, ?)",
            users_data
        )
        
        # Заполнение остатков на складе
        import random
        
        # Получаем ID филиалов и картриджей
        cursor.execute("SELECT id FROM branches")
        branch_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM cartridge_types")
        cartridge_ids = [row[0] for row in cursor.fetchall()]
        
        # Создаем более реалистичные остатки
        stock_data = []
        for branch_id in branch_ids:
            for cartridge_id in cartridge_ids:
                # Больше остатков у крупных филиалов, меньше у отделений
                if branch_id <= 10:  # Основные филиалы
                    quantity = random.randint(10, 100)
                elif branch_id <= 20:  # Городские отделения
                    quantity = random.randint(5, 50)
                else:  # Административные подразделения
                    quantity = random.randint(0, 20)
                    
                stock_data.append((branch_id, cartridge_id, quantity))
        
        cursor.executemany(
            "INSERT OR IGNORE INTO stock_items (branch_id, cartridge_type_id, quantity) VALUES (?, ?, ?)",
            stock_data
        )
        
        # Создание реалистичных заявок
        cursor.execute("SELECT id FROM users WHERE role = 'branch_user'")
        branch_user_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM users WHERE role = 'executor'")
        executor_ids = [row[0] for row in cursor.fetchall()]
        
        test_requests = [
            ('REQ-20250103-001', branch_ids[0], branch_user_ids[0], 'high', 'new', 'Срочная заявка на картриджи HP для медицинского принтера в приемном отделении'),
            ('REQ-20250103-002', branch_ids[1], branch_user_ids[1], 'normal', 'in_progress', 'Плановая замена картриджей Canon в административном корпусе'),
            ('REQ-20250103-003', branch_ids[2], branch_user_ids[2], 'low', 'done', 'Заказ расходных материалов Samsung для архивного отдела'),
            ('REQ-20250103-004', branch_ids[10], branch_user_ids[3], 'high', 'new', 'Экстренная потребность в картриджах Brother для рентген-кабинета'),
            ('REQ-20250103-005', branch_ids[20], branch_user_ids[0], 'normal', 'new', 'Заявка на картриджи Xerox для поликлинического отделения'),
        ]
        
        for i, req_data in enumerate(test_requests):
            cursor.execute(
                """INSERT OR IGNORE INTO requests 
                   (request_code, branch_id, user_id, priority, status, comment, assigned_executor_id) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (*req_data, executor_ids[i % len(executor_ids)] if req_data[4] != 'new' else None)
            )
        
        # Элементы заявок
        cursor.execute("SELECT id FROM requests")
        request_ids = [row[0] for row in cursor.fetchall()]
        
        request_items_data = [
            (request_ids[0], cartridge_ids[0], 3),  # 3 HP-CF248A
            (request_ids[0], cartridge_ids[1], 2),  # 2 HP-CE285A
            (request_ids[1], cartridge_ids[3], 4),  # 4 CANON-728
            (request_ids[1], cartridge_ids[4], 2),  # 2 CANON-725
            (request_ids[2], cartridge_ids[10], 1), # 1 SAMSUNG-MLT-D111S
            (request_ids[3], cartridge_ids[8], 5),  # 5 BROTHER-TN2090
            (request_ids[4], cartridge_ids[6], 2),  # 2 XEROX-3020
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO request_items (request_id, cartridge_type_id, quantity) VALUES (?, ?, ?)",
            request_items_data
        )
        
        # Логи изменений
        logs_data = [
            (request_ids[0], branch_user_ids[0], 'created', None, 'new', 'Заявка создана пользователем Сургутского филиала'),
            (request_ids[1], branch_user_ids[1], 'created', None, 'new', 'Заявка создана пользователем Нижневартовского филиала'),
            (request_ids[1], executor_ids[0], 'status_changed', 'new', 'in_progress', 'Заявка принята в работу исполнителем'),
            (request_ids[2], branch_user_ids[2], 'created', None, 'new', 'Заявка создана пользователем Нефтеюганского филиала'),
            (request_ids[2], executor_ids[1], 'status_changed', 'new', 'in_progress', 'Заявка обработана'),
            (request_ids[2], executor_ids[1], 'status_changed', 'in_progress', 'done', 'Заявка выполнена, картриджи переданы'),
            (request_ids[3], branch_user_ids[3], 'created', None, 'new', 'Экстренная заявка от медицинского отделения'),
            (request_ids[4], branch_user_ids[0], 'created', None, 'new', 'Плановая заявка от поликлиники'),
        ]
        
        cursor.executemany(
            """INSERT OR IGNORE INTO logs 
               (request_id, user_id, action, from_status, to_status, note) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            logs_data
        )
        
        conn.commit()
        print("✅ База данных успешно заполнена реальными филиалами ХМАО!")
        print(f"📊 Создано:")
        print(f"   - Филиалов и отделений: {len(branches_data)}")
        print(f"   - Типов картриджей: {len(cartridge_types_data)}")
        print(f"   - Пользователей: {len(users_data)}")
        print(f"   - Остатков на складе: {len(stock_data)}")
        print(f"   - Заявок: {len(test_requests)}")
        print(f"   - Позиций в заявках: {len(request_items_data)}")
        print(f"   - Записей в логах: {len(logs_data)}")
        
        # Показываем статистику по филиалам
        print("\n🏢 Структура филиалов:")
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN code LIKE 'F-%' THEN 'Основные филиалы'
                    WHEN code LIKE 'OTD-%' THEN 'Территориальные отделения'
                    WHEN code LIKE 'АУ-%' THEN 'Аппарат управления'
                    ELSE 'Прочие'
                END as type,
                COUNT(*) as count
            FROM branches 
            GROUP BY 
                CASE 
                    WHEN code LIKE 'F-%' THEN 'Основные филиалы'
                    WHEN code LIKE 'OTD-%' THEN 'Территориальные отделения'
                    WHEN code LIKE 'АУ-%' THEN 'Аппарат управления'
                    ELSE 'Прочие'
                END
        """)
        
        stats = cursor.fetchall()
        for stat in stats:
            print(f"   - {stat[0]}: {stat[1]} шт.")
        
    except Exception as e:
        print(f"❌ Ошибка при заполнении БД: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database_with_real_branches()