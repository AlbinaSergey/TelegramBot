-- HelpDesk System Database Schema (Extended)
-- Расширенная схема для судебно-медицинского учреждения ХМАО
-- Система заявок на картриджи с интеграцией Telegram

-- users: пользователи системы, по умолчанию их в Telegram идентифицируем по telegram_id
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER UNIQUE NOT NULL,
  username TEXT,
  full_name TEXT,
  role TEXT NOT NULL CHECK(role IN ('admin','executor','branch_user')),
  password_hash TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- branches: филиалы и отделения (расширенная версия)
CREATE TABLE IF NOT EXISTS branches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,   -- сокращение филиала (F-KAZ, OTD-GIST-HM)
  name TEXT NOT NULL,
  full_name TEXT,              -- полное название
  type TEXT NOT NULL CHECK(type IN ('zone','branch','department','administration')), 
  address TEXT,                -- полный адрес
  city TEXT,
  postal_code TEXT,
  phone TEXT,
  phone_registry TEXT,         -- телефон регистратуры
  phone_manager TEXT,          -- телефон заведующего
  email TEXT,
  manager_name TEXT,           -- ФИО заведующего
  work_schedule TEXT,          -- график работы
  parent_branch_id INTEGER REFERENCES branches(id), -- для иерархии (отделение -> зональный отдел)
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- cartridge types (справочник картриджей)
CREATE TABLE IF NOT EXISTS cartridge_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  compatible_printers TEXT,     -- список совместимых принтеров
  vendor TEXT,                  -- производитель (HP, Canon, Xerox)
  is_active BOOLEAN NOT NULL DEFAULT 1
);

-- склад: остатки и списания
CREATE TABLE IF NOT EXISTS stock_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL DEFAULT 0,
  reserved_quantity INTEGER NOT NULL DEFAULT 0, -- зарезервировано для заявок
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(branch_id, cartridge_type_id)
);

-- заявки (orders/tickets)
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_code TEXT UNIQUE NOT NULL,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  priority TEXT NOT NULL CHECK(priority IN ('low','normal','high','urgent')),
  status TEXT NOT NULL DEFAULT 'new',  -- new, in_progress, approved, delivered, done, cancelled, archived
  comment TEXT,
  delivery_address TEXT,        -- адрес доставки (если отличается)
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  assigned_executor_id INTEGER REFERENCES users(id),
  approved_at DATETIME,
  delivered_at DATETIME,
  completed_at DATETIME,
  sla_deadline DATETIME,        -- крайний срок по SLA
  sla_notified_at DATETIME
);

-- элементы заявки (заказанный картридж)
CREATE TABLE IF NOT EXISTS request_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL CHECK(quantity>0),
  delivered_quantity INTEGER DEFAULT 0,
  unit_price DECIMAL(10,2),     -- цена за единицу
  total_price DECIMAL(10,2)     -- общая стоимость
);

-- аудит-дневник изменений
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id),
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  action TEXT NOT NULL,        -- e.g. 'created', 'status_changed', 'assigned', 'approved'
  from_status TEXT,
  to_status TEXT,
  field_name TEXT,             -- какое поле изменилось
  old_value TEXT,              -- старое значение
  new_value TEXT,              -- новое значение
  note TEXT,
  ip_address TEXT              -- IP для аудита
);

-- уведомления и SLA
CREATE TABLE IF NOT EXISTS notifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id),
  type TEXT NOT NULL CHECK(type IN ('sla_warning','sla_violation','status_change','assignment')),
  message TEXT NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT 0,
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  telegram_message_id INTEGER  -- ID сообщения в Telegram
);

-- метаинформация для интеграции 1С (опционально)
CREATE TABLE IF NOT EXISTS one_c_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  taken_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  snapshot_json TEXT,
  sync_status TEXT DEFAULT 'pending' CHECK(sync_status IN ('pending','synced','error'))
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_branch ON requests(branch_id);
CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at);
CREATE INDEX IF NOT EXISTS idx_requests_assigned ON requests(assigned_executor_id);
CREATE INDEX IF NOT EXISTS idx_logs_request ON logs(request_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_stock_branch ON stock_items(branch_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_branches_type ON branches(type);
CREATE INDEX IF NOT EXISTS idx_branches_parent ON branches(parent_branch_id);