#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script from SQLite to PostgreSQL
Миграция данных из SQLite в PostgreSQL
"""

import sqlite3
import psycopg2
import json
import os
from datetime import datetime

class DatabaseMigrator:
    def __init__(self, sqlite_path, postgres_config):
        self.sqlite_path = sqlite_path
        self.postgres_config = postgres_config
        
    def get_postgresql_schema(self):
        """Преобразование SQLite схемы в PostgreSQL"""
        return """
-- HelpDesk System Database Schema for PostgreSQL
-- Система заявок на картриджи с интеграцией Telegram

-- users: пользователи системы, по умолчанию их в Telegram идентифицируем по telegram_id
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  role TEXT NOT NULL CHECK(role IN ('admin','executor','branch_user')),
  password_hash TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- branches: филиалы и отделения
CREATE TABLE IF NOT EXISTS branches (
  id SERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,   -- сокращение филиала (F‑KAZ, ГОРОД‑12)
  name TEXT NOT NULL,
  city TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- cartridge types (справочник картриджей)
CREATE TABLE IF NOT EXISTS cartridge_types (
  id SERIAL PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

-- склад: остатки и списания
CREATE TABLE IF NOT EXISTS stock_items (
  id SERIAL PRIMARY KEY,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL DEFAULT 0,
  UNIQUE(branch_id, cartridge_type_id)
);

-- заявки (orders/tickets)
CREATE TABLE IF NOT EXISTS requests (
  id SERIAL PRIMARY KEY,
  request_code TEXT UNIQUE NOT NULL,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
  status TEXT NOT NULL DEFAULT 'new',  -- new, in_progress, done, cancelled, archived
  comment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  assigned_executor_id INTEGER REFERENCES users(id),
  sla_notified_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- элементы заявки (заказанный картридж)
CREATE TABLE IF NOT EXISTS request_items (
  id SERIAL PRIMARY KEY,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL CHECK(quantity>0)
);

-- аудит-дневник изменений
CREATE TABLE IF NOT EXISTS logs (
  id SERIAL PRIMARY KEY,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id),
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  action TEXT NOT NULL,        -- e.g. 'created', 'status_changed', 'assigned'
  from_status TEXT,
  to_status TEXT,
  note TEXT
);

-- метаинформация для интеграции 1С (опционально)
-- сохраняется остаток на момент заявки
CREATE TABLE IF NOT EXISTS one_c_snapshot (
  id SERIAL PRIMARY KEY,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  taken_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  snapshot_json JSONB
);

-- Индексы для оптимизации производительности
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_branches_code ON branches(code);
CREATE INDEX IF NOT EXISTS idx_cartridge_types_sku ON cartridge_types(sku);
CREATE INDEX IF NOT EXISTS idx_stock_items_branch ON stock_items(branch_id);
CREATE INDEX IF NOT EXISTS idx_stock_items_cartridge ON stock_items(cartridge_type_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_branch ON requests(branch_id);
CREATE INDEX IF NOT EXISTS idx_requests_user ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_executor ON requests(assigned_executor_id);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_request_items_request ON request_items(request_id);
CREATE INDEX IF NOT EXISTS idx_logs_request ON logs(request_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
"""

    def migrate_data(self):
        """Основная функция миграции"""
        print("🚀 Начинаем миграцию из SQLite в PostgreSQL...")
        
        # Подключение к базам данных
        sqlite_conn = sqlite3.connect(self.sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row  # для доступа по именам колонок
        
        pg_conn = psycopg2.connect(**self.postgres_config)
        pg_cursor = pg_conn.cursor()
        
        try:
            # Создание структуры в PostgreSQL
            print("📋 Создание структуры таблиц в PostgreSQL...")
            pg_cursor.execute(self.get_postgresql_schema())
            pg_conn.commit()
            
            # Миграция данных по таблицам
            tables_order = [
                'branches',
                'cartridge_types', 
                'users',
                'stock_items',
                'requests',
                'request_items',
                'logs',
                'one_c_snapshot'
            ]
            
            for table in tables_order:
                self.migrate_table(sqlite_conn, pg_cursor, table)
                pg_conn.commit()
                print(f"✅ Таблица {table} мигрирована")
            
            print("🎉 Миграция завершена успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            pg_conn.rollback()
            
        finally:
            sqlite_conn.close()
            pg_conn.close()
    
    def migrate_table(self, sqlite_conn, pg_cursor, table_name):
        """Миграция отдельной таблицы"""
        # Получение данных из SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"SELECT * FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"⚠️  Таблица {table_name} пуста, пропускаем")
            return
        
        # Получение имен колонок (исключая id для SERIAL)
        columns = [description[0] for description in sqlite_cursor.description]
        columns_without_id = [col for col in columns if col != 'id']
        
        # Создание запроса для вставки
        placeholders = ', '.join(['%s'] * len(columns_without_id))
        columns_str = ', '.join(columns_without_id)
        
        insert_query = f"""
            INSERT INTO {table_name} ({columns_str}) 
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """
        
        # Подготовка данных для вставки
        data_to_insert = []
        for row in rows:
            row_data = []
            for col in columns_without_id:
                value = row[col]
                
                # Специальная обработка для JSON полей
                if table_name == 'one_c_snapshot' and col == 'snapshot_json':
                    # Проверяем, является ли значение валидным JSON
                    if value:
                        try:
                            json.loads(value)  # проверка валидности
                        except:
                            value = json.dumps({"raw_data": value})
                
                row_data.append(value)
            
            data_to_insert.append(tuple(row_data))
        
        # Вставка данных
        pg_cursor.executemany(insert_query, data_to_insert)
        
        # Обновление последовательности для SERIAL полей
        pg_cursor.execute(f"""
            SELECT setval(pg_get_serial_sequence('{table_name}', 'id'), 
                         COALESCE(MAX(id), 1)) 
            FROM {table_name}
        """)
        
        print(f"📊 {table_name}: мигрировано {len(data_to_insert)} записей")

def load_postgres_config():
    """Загрузка конфигурации PostgreSQL из переменных окружения"""
    return {
        'host': os.getenv('PG_HOST', 'localhost'),
        'port': os.getenv('PG_PORT', '5432'),
        'database': os.getenv('PG_DATABASE', 'helpdesk'),
        'user': os.getenv('PG_USER', 'helpdesk_user'),
        'password': os.getenv('PG_PASSWORD', 'helpdesk_password')
    }

def main():
    """Основная функция"""
    sqlite_path = os.getenv('SQLITE_PATH', 'database/helpdesk.db')
    postgres_config = load_postgres_config()
    
    print("🔧 Конфигурация миграции:")
    print(f"   SQLite: {sqlite_path}")
    print(f"   PostgreSQL: {postgres_config['user']}@{postgres_config['host']}:{postgres_config['port']}/{postgres_config['database']}")
    
    # Проверка существования SQLite файла
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite файл не найден: {sqlite_path}")
        return
    
    migrator = DatabaseMigrator(sqlite_path, postgres_config)
    migrator.migrate_data()

if __name__ == "__main__":
    main()