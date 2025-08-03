-- Улучшенная схема БД для системы управления картриджами
-- Более компактная и функциональная версия

-- Пользователи системы
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER UNIQUE NOT NULL,
  username TEXT,
  role TEXT NOT NULL DEFAULT 'branch_user' CHECK(role IN ('admin','executor','branch_user')),
  password_hash TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Филиалы и отделения
CREATE TABLE IF NOT EXISTS branches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,   -- сокращение филиала (F‑KAZ, ГОРОД‑12)
  name TEXT NOT NULL,
  city TEXT,
  is_active BOOLEAN NOT NULL DEFAULT 1
);

-- Справочник картриджей
CREATE TABLE IF NOT EXISTS cartridge_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL
);

-- Склад: остатки и списания (упрощено)
CREATE TABLE IF NOT EXISTS stock_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id) ON DELETE CASCADE,
  quantity INTEGER NOT NULL DEFAULT 0 CHECK(quantity >= 0),
  UNIQUE(branch_id, cartridge_type_id)
);

-- Заявки (объединены с элементами заявки)
CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_code TEXT UNIQUE NOT NULL,
  branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  priority TEXT NOT NULL DEFAULT 'normal' CHECK(priority IN ('low','normal','high')),
  status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','in_progress','done','cancelled','archived')),
  comment TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  assigned_executor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  sla_notified_at DATETIME,
  completed_at DATETIME,
  -- Встроенные элементы заявки как JSON
  items_json TEXT NOT NULL DEFAULT '[]' CHECK(json_valid(items_json))
);

-- Аудит-дневник изменений (упрощен)
CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  action TEXT NOT NULL,
  details_json TEXT DEFAULT '{}' CHECK(json_valid(details_json))
);

-- Метаинформация для интеграции 1С (опционально)
CREATE TABLE IF NOT EXISTS one_c_snapshot (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
  taken_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  snapshot_json TEXT NOT NULL CHECK(json_valid(snapshot_json))
);

-- Индексы для оптимизации
CREATE INDEX IF NOT EXISTS idx_requests_branch_status ON requests(branch_id, status);
CREATE INDEX IF NOT EXISTS idx_requests_user ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_executor ON requests(assigned_executor_id);
CREATE INDEX IF NOT EXISTS idx_logs_request_timestamp ON logs(request_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_stock_branch_cartridge ON stock_items(branch_id, cartridge_type_id);

-- Представления для упрощения запросов
CREATE VIEW IF NOT EXISTS v_active_requests AS
SELECT 
  r.id, r.request_code, r.priority, r.status, r.comment, r.created_at,
  r.completed_at, r.assigned_executor_id,
  b.code as branch_code, b.name as branch_name,
  u.username as requester_username,
  e.username as executor_username,
  json_array_length(r.items_json) as items_count
FROM requests r
JOIN branches b ON r.branch_id = b.id
JOIN users u ON r.user_id = u.id
LEFT JOIN users e ON r.assigned_executor_id = e.id
WHERE r.status NOT IN ('archived', 'cancelled')
  AND b.is_active = 1;

CREATE VIEW IF NOT EXISTS v_stock_summary AS
SELECT 
  b.code as branch_code, b.name as branch_name,
  ct.sku, ct.name as cartridge_name,
  si.quantity,
  CASE 
    WHEN si.quantity = 0 THEN 'out_of_stock'
    WHEN si.quantity <= 5 THEN 'low_stock'
    ELSE 'in_stock'
  END as stock_status
FROM stock_items si
JOIN branches b ON si.branch_id = b.id
JOIN cartridge_types ct ON si.cartridge_type_id = ct.id
WHERE b.is_active = 1
ORDER BY b.code, ct.sku;