#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Update cartridge types with real SKU codes
Обновление типов картриджей реальными артикулами
"""

import sqlite3

def update_cartridges(db_path='database/helpdesk.db'):
    """Обновление таблицы картриджей реальными SKU"""
    
    # Реальные картриджи из пользовательского запроса
    CARTRIDGES = ["CE285", "CE278", "CB435", "CB436", "Q2612", "Q5949", "Q7553", "CF283", "106R03623"]
    
    # Расширенная информация о картриджах
    cartridge_types_data = [
        ('CE285A', 'HP 85A LaserJet Pro P1102/P1102w/M1132/M1212/M1217'),
        ('CE278A', 'HP 78A LaserJet Pro P1566/P1606/M1536'),
        ('CB435A', 'HP 35A LaserJet P1005/P1006'),
        ('CB436A', 'HP 36A LaserJet P1505/M1120/M1522'),
        ('Q2612A', 'HP 12A LaserJet 1010/1012/1015/1018/1020/1022/3015/3020/3030/3050/3052/3055'),
        ('Q5949A', 'HP 49A LaserJet 1160/1320/3390/3392'),
        ('Q7553A', 'HP 53A LaserJet P2014/P2015/M2727'),
        ('CF283A', 'HP 83A LaserJet Pro MFP M125/M127/M201/M225'),
        ('106R03623', 'Xerox WorkCentre 3335/3345 (стандартный картридж)'),
    ]
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Очищаем старые данные картриджей
        print("🧹 Очистка старых данных картриджей...")
        cursor.execute("DELETE FROM request_items")
        cursor.execute("DELETE FROM stock_items")
        cursor.execute("DELETE FROM cartridge_types")
        
        # Вставляем новые данные
        print("➕ Добавление новых картриджей...")
        cursor.executemany(
            "INSERT INTO cartridge_types (sku, name) VALUES (?, ?)",
            cartridge_types_data
        )
        
        # Заполняем остатки для всех филиалов
        print("📦 Создание остатков на складе...")
        cursor.execute("SELECT id FROM branches")
        branch_ids = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT id FROM cartridge_types")
        cartridge_ids = [row[0] for row in cursor.fetchall()]
        
        import random
        stock_data = []
        for branch_id in branch_ids:
            for cartridge_id in cartridge_ids:
                # Более реалистичное распределение остатков
                if branch_id <= 10:  # Основные филиалы
                    quantity = random.randint(20, 150)
                elif branch_id <= 25:  # Городские отделения  
                    quantity = random.randint(5, 80)
                else:  # Административные подразделения
                    quantity = random.randint(0, 30)
                    
                stock_data.append((branch_id, cartridge_id, quantity))
        
        cursor.executemany(
            "INSERT INTO stock_items (branch_id, cartridge_type_id, quantity) VALUES (?, ?, ?)",
            stock_data
        )
        
        # Создаем новые заявки с обновленными картриджами
        print("📝 Создание новых заявок...")
        cursor.execute("SELECT id FROM users WHERE role = 'branch_user'")
        branch_user_ids = [row[0] for row in cursor.fetchall()]
        
        new_requests = [
            ('REQ-20250103-NEW-001', branch_ids[0], branch_user_ids[0], 'high', 'new', 'Срочная заявка на картриджи HP CE285A для медицинских принтеров'),
            ('REQ-20250103-NEW-002', branch_ids[1], branch_user_ids[1], 'normal', 'new', 'Плановая замена картриджей CB435A в регистратуре'),
            ('REQ-20250103-NEW-003', branch_ids[5], branch_user_ids[2], 'high', 'new', 'Экстренная потребность в Q2612A для срочной печати документов'),
            ('REQ-20250103-NEW-004', branch_ids[10], branch_user_ids[3], 'normal', 'new', 'Заявка на CF283A для поликлинического отделения'),
        ]
        
        for req_data in new_requests:
            cursor.execute(
                """INSERT INTO requests (request_code, branch_id, user_id, priority, status, comment) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                req_data
            )
        
        # Добавляем позиции в заявки
        cursor.execute("SELECT id FROM requests WHERE request_code LIKE 'REQ-20250103-NEW-%'")
        new_request_ids = [row[0] for row in cursor.fetchall()]
        
        request_items_data = [
            (new_request_ids[0], cartridge_ids[0], 5),  # 5 CE285A
            (new_request_ids[0], cartridge_ids[1], 3),  # 3 CE278A
            (new_request_ids[1], cartridge_ids[2], 4),  # 4 CB435A
            (new_request_ids[1], cartridge_ids[3], 2),  # 2 CB436A
            (new_request_ids[2], cartridge_ids[4], 8),  # 8 Q2612A
            (new_request_ids[2], cartridge_ids[5], 2),  # 2 Q5949A
            (new_request_ids[3], cartridge_ids[7], 3),  # 3 CF283A
            (new_request_ids[3], cartridge_ids[8], 1),  # 1 106R03623
        ]
        
        cursor.executemany(
            "INSERT INTO request_items (request_id, cartridge_type_id, quantity) VALUES (?, ?, ?)",
            request_items_data
        )
        
        # Добавляем логи для новых заявок
        logs_data = []
        for i, req_id in enumerate(new_request_ids):
            logs_data.append((req_id, branch_user_ids[i % len(branch_user_ids)], 'created', None, 'new', f'Заявка создана с обновленными картриджами'))
        
        cursor.executemany(
            """INSERT INTO logs (request_id, user_id, action, from_status, to_status, note) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            logs_data
        )
        
        conn.commit()
        
        print("✅ Картриджи успешно обновлены!")
        print(f"📊 Обновлено:")
        print(f"   - Типов картриджей: {len(cartridge_types_data)}")
        print(f"   - Остатков на складе: {len(stock_data)}")
        print(f"   - Новых заявок: {len(new_requests)}")
        print(f"   - Позиций в заявках: {len(request_items_data)}")
        
        # Показываем обновленный список картриджей
        print("\n🖨️ Список картриджей в системе:")
        cursor.execute("SELECT sku, name FROM cartridge_types ORDER BY sku")
        cartridges = cursor.fetchall()
        for cart in cartridges:
            print(f"   - {cart[0]}: {cart[1]}")
        
        # Показываем статистику остатков
        print("\n📈 Статистика остатков (топ-5 филиалов):")
        cursor.execute("""
            SELECT b.name, SUM(s.quantity) as total_stock
            FROM stock_items s
            JOIN branches b ON s.branch_id = b.id
            GROUP BY b.id, b.name
            ORDER BY total_stock DESC
            LIMIT 5
        """)
        top_stocks = cursor.fetchall()
        for stock in top_stocks:
            print(f"   - {stock[0]}: {stock[1]} шт.")
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении картриджей: {e}")
        conn.rollback()
        
    finally:
        conn.close()

if __name__ == "__main__":
    update_cartridges()