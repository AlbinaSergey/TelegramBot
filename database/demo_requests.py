#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for HelpDesk cartridge request system
Демонстрационный скрипт работы системы заявок на картриджи
"""

from db_utils import HelpDeskDB

def demo_cartridge_system():
    """Демонстрация работы системы заявок на картриджи"""
    
    db = HelpDeskDB()
    
    print("=" * 60)
    print("🖨️  СИСТЕМА ЗАЯВОК НА КАРТРИДЖИ - ДЕМОНСТРАЦИЯ")
    print("=" * 60)
    
    # 1. Показываем список филиалов
    print("\n🏢 ФИЛИАЛЫ И ОТДЕЛЕНИЯ ХМАО:")
    branches = db.get_branches()
    
    # Группируем по типам
    main_branches = [b for b in branches if b['code'].startswith('F-')]
    departments = [b for b in branches if b['code'].startswith('OTD-')]
    administration = [b for b in branches if b['code'].startswith('АУ-')]
    
    print(f"\n📍 Основные филиалы ({len(main_branches)}):")
    for branch in main_branches[:5]:  # показываем первые 5
        print(f"   • {branch['code']}: {branch['name']} ({branch['city']})")
    if len(main_branches) > 5:
        print(f"   ... и еще {len(main_branches) - 5} филиалов")
    
    print(f"\n🏬 Территориальные отделения ({len(departments)}):")
    for dept in departments[:5]:
        print(f"   • {dept['code']}: {dept['name']} ({dept['city']})")
    if len(departments) > 5:
        print(f"   ... и еще {len(departments) - 5} отделений")
    
    print(f"\n🏛️ Аппарат управления ({len(administration)}):")
    for admin in administration:
        print(f"   • {admin['code']}: {admin['name']}")
    
    # 2. Показываем доступные картриджи
    print("\n🖨️ ДОСТУПНЫЕ КАРТРИДЖИ:")
    cartridges = db.get_cartridge_types()
    for cart in cartridges:
        print(f"   • {cart['sku']}: {cart['name']}")
    
    # 3. Показываем остатки на складе для одного из филиалов
    print(f"\n📦 ОСТАТКИ НА СКЛАДЕ ({main_branches[0]['name']}):")
    stock = db.get_stock_by_branch(main_branches[0]['id'])
    for item in stock:
        status = "✅ В наличии" if item['quantity'] > 10 else "⚠️ Мало" if item['quantity'] > 0 else "❌ Нет"
        print(f"   • {item['sku']}: {item['quantity']} шт. {status}")
    
    # 4. Создаем новую заявку
    print("\n📝 СОЗДАНИЕ НОВОЙ ЗАЯВКИ:")
    
    # Получаем пользователя филиала
    user = db.get_user_by_telegram_id(300000001)  # branch_surgut
    if user:
        # Создаем заявку
        request_code = db.create_request(
            branch_id=main_branches[0]['id'],
            user_id=user['id'],
            priority='normal',
            comment='Демонстрационная заявка на картриджи для офисной техники'
        )
        
        print(f"   ✅ Создана заявка: {request_code}")
        
        # Добавляем позиции в заявку
        db.add_request_item(request_code, cartridges[0]['id'], 3)  # 3 шт первого картриджа
        db.add_request_item(request_code, cartridges[1]['id'], 2)  # 2 шт второго картриджа
        
        print(f"   📦 Добавлены позиции:")
        print(f"      - {cartridges[0]['sku']}: 3 шт.")
        print(f"      - {cartridges[1]['sku']}: 2 шт.")
        
        # Показываем детали заявки
        request_details = db.get_request_by_code(request_code)
        items = db.get_request_items(request_code)
        
        print(f"\n📋 ДЕТАЛИ ЗАЯВКИ {request_code}:")
        print(f"   • Филиал: {request_details['branch_name']}")
        print(f"   • Пользователь: {request_details['user_name']}")
        print(f"   • Приоритет: {request_details['priority']}")
        print(f"   • Статус: {request_details['status']}")
        print(f"   • Комментарий: {request_details['comment']}")
        print(f"   • Создана: {request_details['created_at']}")
        
        print(f"\n   📦 Позиции заявки:")
        for item in items:
            print(f"      - {item['sku']}: {item['quantity']} шт. ({item['cartridge_name']})")
    
    # 5. Показываем заявки по филиалу
    print(f"\n📊 ЗАЯВКИ ПО ФИЛИАЛУ ({main_branches[0]['name']}):")
    branch_requests = db.get_requests_by_branch(main_branches[0]['id'])
    
    for req in branch_requests[-5:]:  # последние 5 заявок
        status_icon = {
            'new': '🆕',
            'in_progress': '⏳',
            'done': '✅',
            'cancelled': '❌',
            'archived': '📁'
        }.get(req['status'], '❓')
        
        priority_icon = {
            'low': '🟢',
            'normal': '🟡', 
            'high': '🔴'
        }.get(req['priority'], '⚪')
        
        print(f"   {status_icon} {req['request_code']} | {priority_icon} {req['priority']} | {req['username']} | {req['total_items'] or 0} поз.")
    
    # 6. Показываем общую статистику
    print("\n📈 ОБЩАЯ СТАТИСТИКА СИСТЕМЫ:")
    stats = db.get_stats()
    
    print(f"   • Всего заявок: {stats['total_requests']}")
    print(f"   • Активных пользователей: {stats['active_users']}")
    print(f"   • Активных филиалов: {stats['active_branches']}")
    
    print(f"\n   📊 По статусам:")
    for status, count in stats['by_status'].items():
        icon = {
            'new': '🆕',
            'in_progress': '⏳', 
            'done': '✅',
            'cancelled': '❌',
            'archived': '📁'
        }.get(status, '❓')
        print(f"      {icon} {status}: {count}")
    
    print(f"\n   🎯 По приоритетам:")
    for priority, count in stats['by_priority'].items():
        icon = {
            'low': '🟢',
            'normal': '🟡',
            'high': '🔴'
        }.get(priority, '⚪')
        print(f"      {icon} {priority}: {count}")
    
    # 7. Проверяем SLA нарушения
    sla_violations = db.get_sla_violations(1)  # заявки старше 1 часа
    if sla_violations:
        print(f"\n⚠️ SLA НАРУШЕНИЯ ({len(sla_violations)}):")
        for violation in sla_violations:
            print(f"   🚨 {violation['request_code']} - {violation['branch_name']} (создана: {violation['created_at']})")
    else:
        print("\n✅ SLA НАРУШЕНИЙ НЕТ")
    
    print("\n" + "=" * 60)
    print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("=" * 60)

if __name__ == "__main__":
    demo_cartridge_system()