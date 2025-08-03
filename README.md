# 🛠️ HelpDesk Ecosystem: Telegram Bot + Web + MiniApp

Полнофункциональная система обработки заявок для организаций с распределённой структурой (филиалы, склады, администрация).  
Проект создан как единая точка входа для всех типов заявок: заказ картриджей, ремонт техники, обслуживание, IT-помощь и т.д.

---

## 🚀 Особенности

- 📦 **Заказы картриджей**: Telegram-бот, MiniApp и Web-панель
- 📊 **Web-отчёты и фильтры**: аналитика по филиалам, количеству, срокам
- 🧑‍💼 **Ролевой доступ**: администраторы, кладовщики, филиалы
- 📡 **Уведомления**: Telegram + SLA-напоминания + (в будущем email)
- 🔄 **Интеграции**: поддержка 1С (остатки), SMTP (почта), экспорт в Excel
- 📁 **Миграции**: из SQLite → PostgreSQL в любой момент
- 🧩 **Расширяемость**: структура проекта разделена по модулям

---

## 🧩 Структура проекта

```bash
project/
├── bot/                  # Telegram-бот: FSM, логика
│   ├── handlers/         # Хэндлеры по функциям
│   ├── keyboards/        # Инлайн / reply кнопки
│   ├── utils/            # FSM, генерация ID, валидации
│   └── main.py
├── webpanel/             # Django Admin / Web UI
│   ├── views/            # API и UI-представления
│   ├── templates/        # HTML-шаблоны
│   └── admin.py
├── miniapp/              # Telegram Mini App (WebView)
│   ├── components/       # UI-компоненты
│   └── app.js
├── database/
│   ├── schema.sql        # Структура БД
│   ├── seed.py           # Начальные данные
│   ├── migrate.py        # Экспорт в PostgreSQL
│   └── archive_policy.json
├── cron/
│   ├── backup.sh         # Бэкапы базы
│   ├── sla_notify.py     # SLA-напоминания
│   └── cleanup.sh        # Очистка старых резервов
├── integrations/
│   ├── one_c_connector.py  # Остатки из 1С
│   └── smtp_client.py      # Email-уведомления
├── utils/
│   ├── logger.py         # Логирование
│   └── formatter.py      # Дата, числовые форматы
├── tests/
│   ├── test_bot.py
│   ├── test_web.py
│   └── test_database.py
├── .env                  # Переменные окружения
├── requirements.txt      # pip-зависимости
├── README.md             # Описание проекта
└── ROADMAP.md            # Дорожная карта
```

---

## 📦 Установка

```bash
git clone https://github.com/your-org/helpdesk-bot.git
cd helpdesk-bot
pip install -r requirements.txt
cp .env.example .env
python bot/main.py
python manage.py runserver
```

---

## 📈 В ближайших релизах (ROADMAP)

- [x] Заказ картриджей через Telegram и MiniApp
- [x] Уведомление Telegram и SLA-напоминания
- [ ] Web-аналитика по филиалам, Excel-экспорт
- [ ] Интеграция с 1С для проверки остатков
- [ ] Авторизация по Telegram ID + Web login
- [ ] Поддержка PostgreSQL и миграции
- [ ] Email-уведомления и отчёты по расписанию
- [ ] Поддержка заявок на ремонт/обслуживание

---

## 🔐 Безопасность и хранение

- Заявки не удаляются — только архивируются
- Резервные копии: ежедневно + ежегодно
- SLA-мониторинг: уведомления, если не обработано в течение 1 часа
- Telegram ID используется как первичный идентификатор (для отслеживания заявок)

---

## 🤝 Поддержка

- Создано для нужд организаций с распределённой структурой
- Контакты, документация и демо доступны в [ROADMAP.md]
