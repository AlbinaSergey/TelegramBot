#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Complete system demo for HelpDesk with real HMAO data
Демонстрация полной системы заявок на картриджи с реальными данными ХМАО
"""

import sqlite3
from datetime import datetime

def demo_complete_system():
    """Демонстрация полной системы с реальными данными ХМАО"""
    
    conn = sqlite3.connect('database/helpdesk_complete.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("🏥 СИСТЕМА ЗАЯВОК НА КАРТРИДЖИ - БУ 'ХАНТЫ-МАНСИЙСКОЕ БСМ Э'")
    print("=" * 80)
    
    # 1. Структура организации
    print("\n📋 СТРУКТУРА ОРГАНИЗАЦИИ:")
    print("-" * 50)
    
    # Зональные отделы
    cursor.execute("""
        SELECT name, city, manager_name, phone, email 
        FROM branches WHERE type='zone' ORDER BY name
    """)
    zones = cursor.fetchall()
    
    print("🌍 ЗОНАЛЬНЫЕ ОТДЕЛЫ:")
    for zone in zones:
        print(f"   • {zone['name']}")
        print(f"     📍 {zone['city']}")
        print(f"     👤 {zone['manager_name']}")
        print(f"     📞 {zone['phone']}")
        print(f"     ✉️  {zone['email']}")
        print()
    
    # Филиалы по зонам
    cursor.execute("""
        SELECT z.name as zone_name, COUNT(b.id) as branches_count
        FROM branches z
        LEFT JOIN branches b ON b.parent_branch_id = z.id AND b.type = 'branch'
        WHERE z.type = 'zone'
        GROUP BY z.id, z.name
        ORDER BY z.name
    """)
    zone_stats = cursor.fetchall()
    
    print("📊 ФИЛИАЛЫ ПО ЗОНАМ:")
    for stat in zone_stats:
        print(f"   • {stat['zone_name']}: {stat['branches_count']} филиалов")
    
    # Специализированные отделения
    cursor.execute("""
        SELECT name, manager_name, city, phone 
        FROM branches WHERE type='department' ORDER BY city, name
    """)
    departments = cursor.fetchall()
    
    print(f"\n🏥 СПЕЦИАЛИЗИРОВАННЫЕ ОТДЕЛЕНИЯ ({len(departments)}):")
    current_city = ""
    for dept in departments:
        if dept['city'] != current_city:
            current_city = dept['city']
            print(f"\n   📍 {current_city}:")
        
        dept_name = dept['name']
        if len(dept_name) > 60:
            dept_name = dept_name[:57] + "..."
        
        print(f"      • {dept_name}")
        print(f"        👤 {dept['manager_name']}")
        print(f"        📞 {dept['phone']}")
    
    # 2. Картриджи и склад
    print(f"\n\n🖨️  УПРАВЛЕНИЕ КАРТРИДЖАМИ:")
    print("-" * 50)
    
    cursor.execute("""
        SELECT sku, name, vendor, 
               COUNT(si.id) as locations_count,
               SUM(si.quantity) as total_quantity
        FROM cartridge_types ct
        LEFT JOIN stock_items si ON ct.id = si.cartridge_type_id
        GROUP BY ct.id, ct.sku, ct.name, ct.vendor
        ORDER BY ct.vendor, ct.sku
    """)
    cartridges = cursor.fetchall()
    
    print("📦 ДОСТУПНЫЕ КАРТРИДЖИ:")
    current_vendor = ""
    for cart in cartridges:
        if cart['vendor'] != current_vendor:
            current_vendor = cart['vendor']
            print(f"\n   🏷️ {current_vendor}:")
        
        print(f"      • {cart['sku']}: {cart['name'][:50]}...")
        print(f"        📍 Доступно в {cart['locations_count']} точках")
        print(f"        📦 Общий остаток: {cart['total_quantity']} шт.")
    
    # Топ-5 филиалов по остаткам
    cursor.execute("""
        SELECT b.name, b.city, SUM(si.quantity) as total_stock
        FROM branches b
        JOIN stock_items si ON b.id = si.branch_id
        WHERE b.type IN ('branch', 'zone')
        GROUP BY b.id, b.name, b.city
        ORDER BY total_stock DESC
        LIMIT 5
    """)
    top_branches = cursor.fetchall()
    
    print(f"\n📈 ТОП-5 ФИЛИАЛОВ ПО ОСТАТКАМ:")
    for i, branch in enumerate(top_branches, 1):
        print(f"   {i}. {branch['name']} ({branch['city']})")
        print(f"      📦 Общий остаток: {branch['total_stock']} картриджей")
    
    # 3. Заявки и пользователи
    print(f"\n\n📋 СИСТЕМА ЗАЯВОК:")
    print("-" * 50)
    
    # Статистика пользователей
    cursor.execute("""
        SELECT role, COUNT(*) as count
        FROM users
        GROUP BY role
        ORDER BY count DESC
    """)
    user_stats = cursor.fetchall()
    
    print("👥 ПОЛЬЗОВАТЕЛИ СИСТЕМЫ:")
    role_names = {
        'admin': 'Администраторы',
        'executor': 'Исполнители',
        'branch_user': 'Пользователи филиалов'
    }
    
    for stat in user_stats:
        role_name = role_names.get(stat['role'], stat['role'])
        print(f"   • {role_name}: {stat['count']} чел.")
    
    # Статистика заявок
    cursor.execute("""
        SELECT status, priority, COUNT(*) as count
        FROM requests
        GROUP BY status, priority
        ORDER BY status, priority
    """)
    request_stats = cursor.fetchall()
    
    print(f"\n📊 СТАТИСТИКА ЗАЯВОК:")
    if request_stats:
        current_status = ""
        for stat in request_stats:
            if stat['status'] != current_status:
                current_status = stat['status']
                status_names = {
                    'new': 'Новые',
                    'in_progress': 'В работе', 
                    'approved': 'Одобренные',
                    'delivered': 'Доставленные',
                    'done': 'Выполненные'
                }
                print(f"   📌 {status_names.get(current_status, current_status)}:")
            
            priority_names = {
                'low': 'Низкий',
                'normal': 'Обычный',
                'high': 'Высокий',
                'urgent': 'Срочный'
            }
            priority_name = priority_names.get(stat['priority'], stat['priority'])
            print(f"      • {priority_name} приоритет: {stat['count']} заявок")
    else:
        print("   📝 Заявки отсутствуют")
    
    # Детали заявок
    cursor.execute("""
        SELECT r.request_code, r.status, r.priority, r.comment,
               b.name as branch_name, b.city,
               u.full_name as user_name,
               r.created_at,
               GROUP_CONCAT(ct.sku || ' x' || ri.quantity, ', ') as items
        FROM requests r
        JOIN branches b ON r.branch_id = b.id
        JOIN users u ON r.user_id = u.id
        LEFT JOIN request_items ri ON r.id = ri.request_id
        LEFT JOIN cartridge_types ct ON ri.cartridge_type_id = ct.id
        GROUP BY r.id
        ORDER BY r.created_at DESC
        LIMIT 5
    """)
    recent_requests = cursor.fetchall()
    
    if recent_requests:
        print(f"\n📋 ПОСЛЕДНИЕ ЗАЯВКИ:")
        for req in recent_requests:
            status_emoji = {
                'new': '🆕',
                'in_progress': '⏳',
                'approved': '✅',
                'delivered': '🚚',
                'done': '✅'
            }
            
            priority_emoji = {
                'low': '🟢',
                'normal': '🟡',
                'high': '🟠',
                'urgent': '🔴'
            }
            
            print(f"\n   {status_emoji.get(req['status'], '📋')} {req['request_code']}")
            print(f"      📍 {req['branch_name']} ({req['city']})")
            print(f"      👤 {req['user_name']}")
            print(f"      {priority_emoji.get(req['priority'], '⚪')} Приоритет: {req['priority']}")
            if req['items']:
                print(f"      📦 Товары: {req['items']}")
            print(f"      💬 {req['comment'][:50]}...")
            print(f"      📅 {req['created_at']}")
    
    # 4. Системная информация
    print(f"\n\n⚙️  СИСТЕМНАЯ ИНФОРМАЦИЯ:")
    print("-" * 50)
    
    # Общая статистика
    cursor.execute("SELECT COUNT(*) FROM branches")
    total_branches = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM cartridge_types")
    total_cartridges = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests")
    total_requests = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(quantity) FROM stock_items")
    total_stock = cursor.fetchone()[0] or 0
    
    print(f"📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"   • Всего подразделений: {total_branches}")
    print(f"   • Типов картриджей: {total_cartridges}")  
    print(f"   • Пользователей: {total_users}")
    print(f"   • Заявок: {total_requests}")
    print(f"   • Картриджей на складах: {total_stock}")
    
    # База данных
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"\n💾 БАЗА ДАННЫХ:")
    print(f"   • Таблиц: {len(tables)}")
    print(f"   • Файл: database/helpdesk_complete.db")
    print(f"   • Схема: database/schema_extended.sql")
    
    print(f"\n🔧 ДОСТУПНЫЕ ОПЕРАЦИИ:")
    print(f"   • Создание заявок через Telegram бот")
    print(f"   • Управление остатками картриджей")
    print(f"   • Отслеживание статусов заявок")
    print(f"   • SLA мониторинг и уведомления")
    print(f"   • Аудит всех изменений")
    print(f"   • Интеграция с 1С")
    
    print("\n" + "=" * 80)
    print("✅ СИСТЕМА ГОТОВА К РАБОТЕ!")
    print("🚀 Можно запускать Telegram бот и начинать обработку заявок")
    print("=" * 80)
    
    conn.close()

if __name__ == "__main__":
    demo_complete_system()