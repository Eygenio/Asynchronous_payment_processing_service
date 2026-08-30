# 💳 Payment Processing Service v0.1.0 — FastAPI + FastStream + RabbitMQ + PostgreSQL

Микросервис для асинхронной обработки платежей. Принимает запросы на оплату, эмулирует внешний платежный шлюз и уведомляет клиента о результате через вебхук.

> ⚠️ Проект реализует только backend-часть.
> Взаимодействие через REST API и брокер сообщений RabbitMQ.

---

## ✨ Возможности

* Создание и получение информации о платежах
* Асинхронная обработка с эмуляцией внешнего шлюза (2–5 сек, 90% успех)
* Отправка вебхуков с повторными попытками
* Надежная доставка событий через Outbox Pattern
* Идемпотентность с помощью ключа идемпотентности
* Dead Letter Queue для необработанных сообщений
* Контейнеризация через Docker и docker-compose
* Интерактивная документация Swagger UI / ReDoc
* Автоматические тесты (unit, e2e)
* Линтеры и проверка типов: ruff, mypy, pre-commit
* Управление зависимостями через uv

---

## 🏗️ Архитектура

Приложение следует принципам **Clean Architecture**:

* **Domain** – бизнес-сущности и абстрактные интерфейсы через `Protocol`
* **Application** – слой сервисов с бизнес-логикой и DTO
* **Infrastructure** – реализации репозиториев, модели SQLAlchemy, Unit of Work
* **Presentation** – FastAPI роутеры, Pydantic-схемы и зависимости

```
project/
├── src/
│ ├── application/
│ │ ├── dto/
│ │ └── services/
│ ├── domain/
│ │ ├── entities.py
│ │ ├── protocols/
│ │ │  └── repositories.py
│ │ └── unit_of_work.py
│ ├── infrastructure/
│ │ ├── models/
│ │ ├── repositories/
│ │ └── unit_of_work.py
│ ├── presentation/
│ │ ├── api/
│ │ ├── schemas/
│ │ └── dependencies.py
│ ├── rabbit/
│ ├── workers/
│ ├── config/
│ ├── db/
│ ├── core/
│ ├── app.py
├── tests/
│ ├── conftest.py
│ ├── factories.py
│ ├── e2e/
│ └── unit/
├── alembic/
├── scripts/
├── docker-compose.yaml
├── Dockerfile
├── pyproject.toml
├── .pre-commit-config.yaml
└── README.md
```

## 🧰 Технологический стек

* **Python** 3.13
* **FastAPI**
* **SQLAlchemy 2.0** (async)
* **PostgreSQL**
* **RabbitMQ** (FastStream)
* **Pydantic** v2
* **Alembic**
* **Docker** и **docker-compose**
* **uv**
* **Pytest**
* **Ruff / MyPy / Pre-commit**
* **Tenacity**
*
---

## 💡 Функциональность

### 💳 Платежи

* `POST /api/v1/payments` – создание платежа
* `GET /api/v1/payments/{payment_id}` – получение информации

### 🔁 Outbox Pattern

При создании платежа транзакционно сохраняется запись в таблице `outbox`. Отдельный воркер `outbox_dispatcher` публикует событие в очередь `payments.new`.

### ⚙️ Consumer

Воркер `payment_consumer` обрабатывает сообщения из очереди, эмулирует платежный шлюз (задержка 2–5 секунд, 90% успех).
После обработки статус платежа и задача на доставку вебхука сохраняются в БД в рамках одной транзакции.
Отправкой вебхуков занимается отдельный воркер `webhook_dispatcher`.

### 🔁 Retry и DLQ

* Повторные попытки отправки вебхуков реализованы с помощью `tenacity`
* Для вебхуков используется отдельная таблица outbox с durable retry-логикой
* Необработанные после 3 попыток сообщения RabbitMQ попадают в Dead Letter Queue

---

# 🚀 Быстрый старт

## 1. Клонирование репозитория

```bash
git clone https://github.com/Eygenio/Asynchronous_payment_processing_service
```

## 2. Настройка окружения

Скопируйте `.env.example` в `.env` и при необходимости измените параметры:
```bash
cp .env.example .env
```

## 3. Запуск через Docker Compose
```bash
docker-compose up --build
```
Сервисы:
API: `http://localhost:8000`
Swagger UI: `http://localhost:8000/docs`
RabbitMQ Management: `http://localhost:15672` (логин/пароль: guest/guest)

---

## 🧪 Тестирование

Запуск unit-тестов:
```bash
uv run pytest
```

E2E-тесты запускаются против реально работающего Docker Compose-стека:
```bash
docker compose up -d
uv run pytest --run-e2e -m e2e
```

После тестов:
```bash
docker compose down
```

---

## 🧹 Проверка кода

```bash
uv run pre-commit run --all-files
uv run ruff check .
uv run ruff format .
uv run mypy src
```

---

## 🔐 Безопасность

* Аутентификация по статическому API-ключу в заголовке `X-API-Key` для всех эндпоинтов `/api/*`
* Пароли и секреты вынесены в `.env`
* База данных и RabbitMQ изолированы внутри Docker-сети
* Webhook URL проверяется перед отправкой, включая защиту от запросов в приватные и зарезервированные сети

---

## 📌 Примеры запросов

Создание платежа:
```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "X-API-Key: test-api-key" \
  -H "Idempotency-Key: 123e4567-e89b-12d3-a456-426614174000" \
  -H "Content-Type: application/json" \
  -d '{
        "amount": 100.50,
        "currency": "USD",
        "description": "Оплата заказа",
        "metadata": {"order_id": "12345"},
        "webhook_url": "https://example.com/webhook"
      }'
```

Ответ `202 Accepted`:
```bash
{
  "payment_id": "8f14e45f-ea6a-4c5b-8c6e-3c8f12e6f9a2",
  "status": "pending",
  "created_at": "2025-01-01T12:00:00Z"
}
```
Получение платежа:
```bash
curl http://localhost:8000/api/v1/payments/8f14e45f-ea6a-4c5b-8c6e-3c8f12e6f9a2 \
  -H "X-API-Key: test-api-key"
```

---
