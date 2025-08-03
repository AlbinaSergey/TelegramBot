-- Триггеры и функции для автоматизации работы с улучшенной схемой

-- Триггер для автоматического создания записей в stock_items при добавлении нового филиала
CREATE TRIGGER IF NOT EXISTS tr_create_stock_for_new_branch
AFTER INSERT ON branches
BEGIN
  INSERT INTO stock_items (branch_id, cartridge_type_id, quantity)
  SELECT NEW.id, ct.id, 0
  FROM cartridge_types ct;
END;

-- Триггер для автоматического создания записей в stock_items при добавлении нового типа картриджа
CREATE TRIGGER IF NOT EXISTS tr_create_stock_for_new_cartridge
AFTER INSERT ON cartridge_types
BEGIN
  INSERT INTO stock_items (branch_id, cartridge_type_id, quantity)
  SELECT b.id, NEW.id, 0
  FROM branches b
  WHERE b.is_active = 1;
END;

-- Триггер для автоматического логирования изменений статуса заявок
CREATE TRIGGER IF NOT EXISTS tr_log_status_changes
AFTER UPDATE ON requests
WHEN OLD.status != NEW.status
BEGIN
  INSERT INTO logs (request_id, user_id, action, details_json)
  VALUES (
    NEW.id,
    COALESCE(NEW.assigned_executor_id, NEW.user_id),
    'status_changed',
    json_object(
      'from_status', OLD.status,
      'to_status', NEW.status,
      'timestamp', datetime('now')
    )
  );
END;

-- Триггер для автоматического логирования создания заявок
CREATE TRIGGER IF NOT EXISTS tr_log_request_created
AFTER INSERT ON requests
BEGIN
  INSERT INTO logs (request_id, user_id, action, details_json)
  VALUES (
    NEW.id,
    NEW.user_id,
    'created',
    json_object(
      'priority', NEW.priority,
      'items_count', json_array_length(NEW.items_json),
      'timestamp', datetime('now')
    )
  );
END;

-- Триггер для автоматического обновления completed_at при завершении заявки
CREATE TRIGGER IF NOT EXISTS tr_update_completed_at
AFTER UPDATE ON requests
WHEN OLD.status != 'done' AND NEW.status = 'done'
BEGIN
  UPDATE requests 
  SET completed_at = datetime('now')
  WHERE id = NEW.id;
END;

-- Функция для проверки доступности картриджей на складе
CREATE VIEW IF NOT EXISTS v_request_availability AS
WITH request_items AS (
  SELECT 
    r.id as request_id,
    r.branch_id,
    json_extract(value, '$.cartridge_type_id') as cartridge_type_id,
    json_extract(value, '$.quantity') as requested_quantity
  FROM requests r
  CROSS JOIN json_each(r.items_json)
  WHERE r.status IN ('new', 'in_progress')
)
SELECT 
  ri.request_id,
  ri.cartridge_type_id,
  ct.sku,
  ct.name as cartridge_name,
  ri.requested_quantity,
  COALESCE(si.quantity, 0) as available_quantity,
  CASE 
    WHEN COALESCE(si.quantity, 0) >= ri.requested_quantity THEN 'available'
    WHEN COALESCE(si.quantity, 0) > 0 THEN 'partial'
    ELSE 'unavailable'
  END as availability_status
FROM request_items ri
JOIN cartridge_types ct ON ri.cartridge_type_id = ct.id
LEFT JOIN stock_items si ON ri.branch_id = si.branch_id AND ri.cartridge_type_id = si.cartridge_type_id;

-- Представление для статистики по заявкам
CREATE VIEW IF NOT EXISTS v_request_stats AS
SELECT 
  b.code as branch_code,
  b.name as branch_name,
  COUNT(*) as total_requests,
  COUNT(CASE WHEN r.status = 'new' THEN 1 END) as new_requests,
  COUNT(CASE WHEN r.status = 'in_progress' THEN 1 END) as in_progress_requests,
  COUNT(CASE WHEN r.status = 'done' THEN 1 END) as completed_requests,
  AVG(CASE WHEN r.completed_at IS NOT NULL 
    THEN julianday(r.completed_at) - julianday(r.created_at) 
    END) as avg_completion_days,
  COUNT(CASE WHEN r.priority = 'high' THEN 1 END) as high_priority_count
FROM requests r
JOIN branches b ON r.branch_id = b.id
WHERE r.created_at >= date('now', '-30 days')
GROUP BY b.id, b.code, b.name
ORDER BY total_requests DESC;

-- Представление для мониторинга SLA
CREATE VIEW IF NOT EXISTS v_sla_monitoring AS
SELECT 
  r.id,
  r.request_code,
  b.code as branch_code,
  r.priority,
  r.status,
  r.created_at,
  r.sla_notified_at,
  CASE 
    WHEN r.priority = 'high' THEN 1  -- 1 день для высокого приоритета
    WHEN r.priority = 'normal' THEN 3 -- 3 дня для обычного приоритета
    ELSE 7  -- 7 дней для низкого приоритета
  END as sla_days,
  CASE 
    WHEN r.priority = 'high' THEN date(r.created_at, '+1 day')
    WHEN r.priority = 'normal' THEN date(r.created_at, '+3 days')
    ELSE date(r.created_at, '+7 days')
  END as sla_deadline,
  CASE 
    WHEN r.status IN ('done', 'cancelled') THEN 'completed'
    WHEN date('now') > CASE 
      WHEN r.priority = 'high' THEN date(r.created_at, '+1 day')
      WHEN r.priority = 'normal' THEN date(r.created_at, '+3 days')
      ELSE date(r.created_at, '+7 days')
    END THEN 'overdue'
    ELSE 'within_sla'
  END as sla_status
FROM requests r
JOIN branches b ON r.branch_id = b.id
WHERE r.status NOT IN ('archived')
ORDER BY sla_status DESC, r.created_at ASC;