-- Примеры использования улучшенной схемы БД

-- 1. Вставка тестовых данных
INSERT INTO users (telegram_id, username, role) VALUES 
(123456789, 'admin_user', 'admin'),
(987654321, 'executor1', 'executor'),
(555666777, 'branch_user1', 'branch_user');

INSERT INTO branches (code, name, city) VALUES 
('F-KAZ', 'Филиал Казахстан', 'Алматы'),
('GOROD-12', 'Городское отделение 12', 'Москва'),
('REG-5', 'Региональное отделение 5', 'Санкт-Петербург');

INSERT INTO cartridge_types (sku, name) VALUES 
('HP-101', 'HP LaserJet 101 картридж'),
('CANON-201', 'Canon PIXMA 201 картридж'),
('EPSON-301', 'Epson WorkForce 301 картридж');

-- 2. Создание заявки с элементами в JSON формате
INSERT INTO requests (
  request_code, 
  branch_id, 
  user_id, 
  priority, 
  comment,
  items_json
) VALUES (
  'REQ-2024-001',
  (SELECT id FROM branches WHERE code = 'F-KAZ'),
  (SELECT id FROM users WHERE telegram_id = 555666777),
  'high',
  'Срочно нужны картриджи для принтеров',
  json_array(
    json_object('cartridge_type_id', 1, 'quantity', 2),
    json_object('cartridge_type_id', 2, 'quantity', 1)
  )
);

-- 3. Обновление остатков на складе
UPDATE stock_items 
SET quantity = 10 
WHERE branch_id = (SELECT id FROM branches WHERE code = 'F-KAZ') 
  AND cartridge_type_id = 1;

-- 4. Назначение исполнителя заявке
UPDATE requests 
SET assigned_executor_id = (SELECT id FROM users WHERE telegram_id = 987654321),
    status = 'in_progress'
WHERE request_code = 'REQ-2024-001';

-- 5. Завершение заявки
UPDATE requests 
SET status = 'done'
WHERE request_code = 'REQ-2024-001';

-- 6. Примеры запросов к представлениям

-- Получение активных заявок
SELECT * FROM v_active_requests;

-- Проверка доступности картриджей для заявок
SELECT * FROM v_request_availability;

-- Статистика по филиалам
SELECT * FROM v_request_stats;

-- Мониторинг SLA
SELECT * FROM v_sla_monitoring WHERE sla_status = 'overdue';

-- Сводка по складу
SELECT * FROM v_stock_summary WHERE stock_status = 'low_stock';

-- 7. Работа с JSON данными

-- Добавление нового элемента в заявку
UPDATE requests 
SET items_json = json_insert(
  items_json, 
  '$[#]', 
  json_object('cartridge_type_id', 3, 'quantity', 1)
)
WHERE request_code = 'REQ-2024-001';

-- Получение всех элементов заявки
SELECT 
  r.request_code,
  json_extract(value, '$.cartridge_type_id') as cartridge_type_id,
  json_extract(value, '$.quantity') as quantity,
  ct.name as cartridge_name
FROM requests r
CROSS JOIN json_each(r.items_json)
JOIN cartridge_types ct ON json_extract(value, '$.cartridge_type_id') = ct.id
WHERE r.request_code = 'REQ-2024-001';

-- 8. Аналитические запросы

-- Топ-5 самых запрашиваемых картриджей
SELECT 
  ct.sku,
  ct.name,
  SUM(json_extract(value, '$.quantity')) as total_requested
FROM requests r
CROSS JOIN json_each(r.items_json)
JOIN cartridge_types ct ON json_extract(value, '$.cartridge_type_id') = ct.id
WHERE r.created_at >= date('now', '-30 days')
GROUP BY ct.id, ct.sku, ct.name
ORDER BY total_requested DESC
LIMIT 5;

-- Среднее время выполнения заявок по приоритетам
SELECT 
  priority,
  COUNT(*) as total_requests,
  AVG(julianday(completed_at) - julianday(created_at)) as avg_days,
  MIN(julianday(completed_at) - julianday(created_at)) as min_days,
  MAX(julianday(completed_at) - julianday(created_at)) as max_days
FROM requests 
WHERE status = 'done' AND completed_at IS NOT NULL
GROUP BY priority;

-- 9. Автоматическое создание записей в stock_items
-- При добавлении нового филиала автоматически создаются записи для всех типов картриджей
INSERT INTO branches (code, name, city) VALUES ('NEW-BRANCH', 'Новый филиал', 'Новосибирск');

-- При добавлении нового типа картриджа автоматически создаются записи для всех филиалов
INSERT INTO cartridge_types (sku, name) VALUES ('NEW-CART', 'Новый картридж');

-- 10. Проверка целостности данных
-- Все заявки должны иметь валидный JSON в items_json
SELECT request_code, items_json 
FROM requests 
WHERE NOT json_valid(items_json);

-- Проверка на отрицательные остатки
SELECT branch_id, cartridge_type_id, quantity 
FROM stock_items 
WHERE quantity < 0;