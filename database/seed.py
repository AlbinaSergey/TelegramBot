#!/usr/bin/env python3
"""
Seed data for HelpDesk Ecosystem Database
Populates initial data for testing and development
"""

import sqlite3
import os
from datetime import datetime

def create_database():
    """Create database and tables if they don't exist"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'helpdesk.db')
    
    # Read and execute schema
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = f.read()
    
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    return conn

def seed_branches(conn):
    """Seed branches data"""
    branches = [
        ('F-KAZ', 'Филиал Казань', 'Казань'),
        ('F-MSK', 'Филиал Москва', 'Москва'),
        ('F-SPB', 'Филиал Санкт-Петербург', 'Санкт-Петербург'),
        ('GOROD-12', 'Городское отделение №12', 'Казань'),
        ('GOROD-15', 'Городское отделение №15', 'Казань'),
        ('MSK-CENTER', 'Московский центр', 'Москва'),
        ('SPB-NEVSKY', 'Невский проспект', 'Санкт-Петербург'),
    ]
    
    cursor = conn.cursor()
    for code, name, city in branches:
        cursor.execute('''
            INSERT OR IGNORE INTO branches (code, name, city, is_active)
            VALUES (?, ?, ?, 1)
        ''', (code, name, city))
    
    print(f"✅ Seeded {len(branches)} branches")

def seed_cartridge_types(conn):
    """Seed cartridge types data"""
    cartridges = [
        ('HP-12A', 'HP 12A (Q2612A) - HP LaserJet Pro'),
        ('HP-49A', 'HP 49A (Q2613A) - HP LaserJet Pro'),
        ('HP-26A', 'HP 26A (Q2610A) - HP LaserJet Pro'),
        ('HP-05A', 'HP 05A (Q2611A) - HP LaserJet Pro'),
        ('CANON-703', 'Canon 703 - Canon LaserShot'),
        ('CANON-704', 'Canon 704 - Canon LaserShot'),
        ('SAMSUNG-ML-2010', 'Samsung ML-2010 - Samsung ML-2010'),
        ('XEROX-106R01259', 'Xerox 106R01259 - Xerox WorkCentre'),
        ('BROTHER-TN-450', 'Brother TN-450 - Brother HL-1110R'),
        ('EPSON-101', 'Epson 101 - Epson Stylus'),
    ]
    
    cursor = conn.cursor()
    for sku, name in cartridges:
        cursor.execute('''
            INSERT OR IGNORE INTO cartridge_types (sku, name)
            VALUES (?, ?)
        ''', (sku, name))
    
    print(f"✅ Seeded {len(cartridges)} cartridge types")

def seed_users(conn):
    """Seed users data"""
    users = [
        # Admin users (replace with actual Telegram IDs)
        (123456789, 'admin_kazan', 'admin'),
        (987654321, 'admin_msk', 'admin'),
        (555666777, 'admin_spb', 'admin'),
        
        # Executors (warehouse workers)
        (111222333, 'executor_kazan', 'executor'),
        (444555666, 'executor_msk', 'executor'),
        (777888999, 'executor_spb', 'executor'),
        
        # Branch users (regular users)
        (100200300, 'user_branch_12', 'branch_user'),
        (400500600, 'user_branch_15', 'branch_user'),
        (700800900, 'user_msk_center', 'branch_user'),
    ]
    
    cursor = conn.cursor()
    for telegram_id, username, role in users:
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, role, is_active)
            VALUES (?, ?, ?, 1)
        ''', (telegram_id, username, role))
    
    print(f"✅ Seeded {len(users)} users")

def seed_stock_items(conn):
    """Seed initial stock data"""
    cursor = conn.cursor()
    
    # Get branch and cartridge IDs
    cursor.execute('SELECT id FROM branches WHERE is_active = 1')
    branch_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT id FROM cartridge_types')
    cartridge_ids = [row[0] for row in cursor.fetchall()]
    
    # Create stock items with random quantities
    import random
    stock_items = []
    for branch_id in branch_ids:
        for cartridge_id in cartridge_ids:
            quantity = random.randint(0, 50)  # Random stock between 0-50
            stock_items.append((branch_id, cartridge_id, quantity))
    
    for branch_id, cartridge_id, quantity in stock_items:
        cursor.execute('''
            INSERT OR REPLACE INTO stock_items (branch_id, cartridge_type_id, quantity)
            VALUES (?, ?, ?)
        ''', (branch_id, cartridge_id, quantity))
    
    print(f"✅ Seeded {len(stock_items)} stock items")

def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    try:
        conn = create_database()
        
        seed_branches(conn)
        seed_cartridge_types(conn)
        seed_users(conn)
        seed_stock_items(conn)
        
        conn.commit()
        print("✅ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()