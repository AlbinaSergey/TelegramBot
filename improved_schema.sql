-- Оптимизированная схема БД для системы управления картриджами

-- Пользователи с расширенным функционалом
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id INTEGER UNIQUE NOT NULL,
  username TEXT,
  full_name TEXT,
  role TEXT NOT NULL DEFAULT 'branch_user' 
    CHECK(role IN ('admin','executor','branch_user','readonly')),
  password_hash TEXT,
  branch_id INTEGER REFERENCES branches(id), -- привязка к филиалу
  settings TEXT DEFAULT '{}', -- JSON настройки (уведомления, язык, etc)
  is_active BOOLEAN NOT NULL DEFAULT 1,
  last_login_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_telegram_id (telegram_id),
  INDEX idx_branch_role (branch_id, role)
);

-- Филиалы с иерархией
CREATE TABLE branches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  city TEXT,
  parent_id INTEGER REFERENCES branches(id), -- для иерархии филиалов
  timezone TEXT DEFAULT 'UTC',
  contact_info TEXT DEFAULT '{}', -- JSON: телефон, адрес, email
  settings TEXT DEFAULT '{}', -- JSON настройки филиала
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_parent (parent_id),
  INDEX idx_city_active (city, is_active)
);

-- Типы картриджей с категориями
CREATE TABLE cartridge_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sku TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  category TEXT, -- например: "laser", "inkjet", "ribbon"
  brand TEXT,
  model TEXT,
  color TEXT,
  is_original BOOLEAN DEFAULT 1, -- оригинал/совместимый
  unit_price DECIMAL(10,2), -- для аналитики
  min_stock_level INTEGER DEFAULT 0, -- минимальный остаток
  is_active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_sku_active (sku, is_active),
  INDEX idx_category_brand (category, brand)
);

-- Остатки с историей движений
CREATE TABLE stock_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL DEFAULT 0,
  reserved_quantity INTEGER NOT NULL DEFAULT 0, -- зарезервировано под заявки
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
  last_sync_1c DATETIME, -- последняя синхронизация с 1С
  
  UNIQUE(branch_id, cartridge_type_id),
  INDEX idx_branch_type (branch_id, cartridge_type_id),
  INDEX idx_low_stock (branch_id) WHERE quantity <= (
    SELECT min_stock_level FROM cartridge_types ct 
    WHERE ct.id = cartridge_type_id
  )
);

-- Заявки с улучшенным статусом
CREATE TABLE requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_code TEXT UNIQUE NOT NULL,
  branch_id INTEGER NOT NULL REFERENCES branches(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  priority TEXT NOT NULL DEFAULT 'normal' 
    CHECK(priority IN ('low','normal','high','urgent')),
  status TEXT NOT NULL DEFAULT 'new' 
    CHECK(status IN ('new','approved','in_progress','delivered','completed','cancelled','rejected')),
  total_items INTEGER DEFAULT 0, -- денормализация для быстрого доступа
  comment TEXT,
  internal_notes TEXT, -- заметки для исполнителей
  delivery_date DATE, -- планируемая дата доставки
  
  -- SLA и уведомления
  sla_hours INTEGER DEFAULT 72, -- SLA в часах
  sla_deadline DATETIME, -- автовычисляемый дедлайн
  sla_notified_at DATETIME,
  
  -- Временные метки
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  assigned_at DATETIME,
  completed_at DATETIME,
  
  -- Исполнители
  assigned_executor_id INTEGER REFERENCES users(id),
  
  INDEX idx_status_priority (status, priority),
  INDEX idx_branch_status (branch_id, status),
  INDEX idx_executor_status (assigned_executor_id, status),
  INDEX idx_sla_deadline (sla_deadline) WHERE status IN ('new','approved','in_progress')
);

-- Элементы заявки без изменений (оптимальная структура)
CREATE TABLE request_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id INTEGER NOT NULL REFERENCES requests(id) ON DELETE CASCADE,
  cartridge_type_id INTEGER NOT NULL REFERENCES cartridge_types(id),
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  delivered_quantity INTEGER DEFAULT 0, -- факт доставки
  unit_price DECIMAL(10,2), -- цена на момент заказа
  
  INDEX idx_request_cartridge (request_id, cartridge_type_id)
);

-- Упрощенный лог с типизированными действиями
CREATE TABLE activity_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL CHECK(entity_type IN ('request','stock','user')),
  entity_id INTEGER NOT NULL,
  user_id INTEGER REFERENCES users(id),
  action_type TEXT NOT NULL, -- 'created','updated','status_changed','assigned','cancelled'
  old_value TEXT, -- JSON предыдущих значений
  new_value TEXT, -- JSON новых значений
  metadata TEXT DEFAULT '{}', -- дополнительная информация
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  INDEX idx_entity (entity_type, entity_id),
  INDEX idx_user_date (user_id, created_at),
  INDEX idx_action_date (action_type, created_at)
);

-- Настройки системы (заменяет отдельные таблицы конфигурации)
CREATE TABLE system_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  description TEXT,
  updated_by INTEGER REFERENCES users(id),
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Триггеры для автоматизации

-- Автообновление updated_at
CREATE TRIGGER update_requests_timestamp 
  AFTER UPDATE ON requests
  FOR EACH ROW
BEGIN
  UPDATE requests SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Автообновление SLA deadline
CREATE TRIGGER calculate_sla_deadline
  AFTER INSERT ON requests
  FOR EACH ROW
BEGIN
  UPDATE requests 
  SET sla_deadline = datetime(created_at, '+' || sla_hours || ' hours')
  WHERE id = NEW.id;
END;

-- Автообновление счетчика элементов заявки
CREATE TRIGGER update_request_items_count
  AFTER INSERT ON request_items
  FOR EACH ROW
BEGIN
  UPDATE requests 
  SET total_items = (
    SELECT COUNT(*) FROM request_items WHERE request_id = NEW.request_id
  )
  WHERE id = NEW.request_id;
END;

CREATE TRIGGER update_request_items_count_delete
  AFTER DELETE ON request_items
  FOR EACH ROW
BEGIN
  UPDATE requests 
  SET total_items = (
    SELECT COUNT(*) FROM request_items WHERE request_id = OLD.request_id
  )
  WHERE id = OLD.request_id;
END;

-- Резервирование товара при создании заявки
CREATE TRIGGER reserve_stock_on_request
  AFTER INSERT ON request_items
  FOR EACH ROW
  WHEN (SELECT status FROM requests WHERE id = NEW.request_id) IN ('new','approved')
BEGIN
  UPDATE stock_items 
  SET reserved_quantity = reserved_quantity + NEW.quantity
  WHERE branch_id = (SELECT branch_id FROM requests WHERE id = NEW.request_id)
    AND cartridge_type_id = NEW.cartridge_type_id;
END;

-- Представления для частых запросов

-- Активные заявки с информацией о филиале и пользователе
CREATE VIEW active_requests AS
SELECT 
  r.*,
  b.name as branch_name,
  b.code as branch_code,
  u.username,
  u.full_name,
  e.username as executor_username,
  CASE 
    WHEN datetime('now') > r.sla_deadline THEN 1 
    ELSE 0 
  END as is_overdue
FROM requests r
JOIN branches b ON r.branch_id = b.id
JOIN users u ON r.user_id = u.id
LEFT JOIN users e ON r.assigned_executor_id = e.id
WHERE r.status NOT IN ('completed','cancelled','archived');

-- Остатки с предупреждениями о низком уровне
CREATE VIEW stock_alerts AS
SELECT 
  si.*,
  b.name as branch_name,
  b.code as branch_code,
  ct.name as cartridge_name,
  ct.sku,
  ct.min_stock_level,
  (si.quantity - si.reserved_quantity) as available_quantity,
  CASE 
    WHEN si.quantity <= ct.min_stock_level THEN 'low'
    WHEN si.quantity = 0 THEN 'empty'
    ELSE 'ok'
  END as stock_status
FROM stock_items si
JOIN branches b ON si.branch_id = b.id
JOIN cartridge_types ct ON si.cartridge_type_id = ct.id
WHERE b.is_active = 1 AND ct.is_active = 1;

-- Начальные данные
INSERT INTO system_settings (key, value, description) VALUES
('default_sla_hours', '72', 'SLA по умолчанию в часах'),
('telegram_bot_token', '', 'Токен Telegram бота'),
('admin_chat_id', '', 'ID чата для уведомлений администраторов'),
('auto_approve_requests', 'false', 'Автоматическое одобрение заявок'),
('low_stock_threshold', '5', 'Пороговое значение для уведомления о низких остатках');