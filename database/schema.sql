-- HelpDesk Ecosystem Database Schema
-- Cartridge Management System with Telegram Integration

-- users: пользователи системы, по умолчанию их в Telegram идентифицируем по telegram_id
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER UNIQUE NOT NULL,
  username TEXT,
  role TEXT NOT NULL CHECK(role IN ('admin','executor','branch_user')),
  password_hash TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- branches: филиалы и отделения
CREATE TABLE IF NOT EXISTS branches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,   -- сокращение филиала (F‑KAZ, ГОРОД‑12)
  name TEXT NOT NULL,
  city TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1
);

-- cartridge types (справочник картриджей)
CREATE TABLE IF NOT EXISTS cartridge_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

-- склад: остатки и списания
CREATE TABLE IF NOT EXISTS stock_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL DEFAULT 0,
  UNIQUE(branch_id, cartridge_type_id)
);

-- заявки (orders/tickets)
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_code TEXT UNIQUE NOT NULL,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  priority TEXT NOT NULL CHECK(priority IN ('low','normal','high')),
  status TEXT NOT NULL DEFAULT 'new',  -- new, in_progress, done, cancelled, archived
  comment TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  assigned_executor_id INTEGER REFERENCES users(id),
  sla_notified_at DATETIME,
  completed_at DATETIME
);

-- элементы заявки (заказанный картридж)
CREATE TABLE IF NOT EXISTS request_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL CHECK(quantity>0)
);

-- аудит-дневник изменений
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id),
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  action TEXT NOT NULL,        -- e.g. 'created', 'status_changed', 'assigned'
  from_status TEXT,
  to_status TEXT,
  note TEXT
);

-- метаинформация для интеграции 1С (опционально)
-- сохраняется остаток на момент заявки
CREATE TABLE IF NOT EXISTS one_c_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  taken_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  snapshot_json TEXT
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_branches_code ON branches(code);
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_branch_id ON requests(branch_id);
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_request_items_request_id ON request_items(request_id);
CREATE INDEX IF NOT EXISTS idx_logs_request_id ON logs(request_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_stock_items_branch_cartridge ON stock_items(branch_id, cartridge_type_id);