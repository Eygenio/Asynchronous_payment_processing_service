# 💳 Payment Processing Service v0.1.0 — FastAPI + FastStream + RabbitMQ + PostgreSQL

Микросервис для асинхронной обработки платежей. Принимает запросы на оплату, эмулирует внешний платежный шлюз и уведомляет клиента о результате через вебхук.

> ⚠️ Проект реализует только backend-часть.
> Взаимодействие через REST API и брокер сообщений RabbitMQ.

---

## ✨ Возможности

* 💸 Создание и получение информации о платежах
* 🔁 Асинхронная обработка с эмуляцией внешнего шлюза (2–5 сек, 90% успех)
* 🔔 Отправка вебхуков с повторными попытками
* 🐇 Надежная доставка событий через Outbox Pattern
* 🔑 Идемпотентность с помощью ключа идемпотентности
* ☠️ Dead Letter Queue для необработанных сообщений
* 📦 Контейнеризация через Docker и docker-compose
* 📡 Интерактивная документация Swagger UI / ReDoc
* 🧪 Автоматические тесты (unit, e2e)
* 🧹 Линтеры и проверка типов: ruff, mypy, pre-commit
* 📝 Управление зависимостями через Poetry

---

## 🏗️ Архитектура

Приложение следует принципам **Clean Architecture**:

* **Domain** – бизнес-сущности и абстрактные интерфейсы репозиториев
* **Application** – слой сервисов с бизнес-логикой
* **Infrastructure** – реализации репозиториев, модели SQLAlchemy, Unit of Work
* **Presentation** – FastAPI роутеры, Pydantic-схемы и зависимости

```
project/
├── src/
│ ├── application/
│ │ └── services/ # Бизнес-логика
│ ├── domain/
│ │ ├── entities.py # Доменные Pydantic-модели
│ │ ├── repositories.py # Интерфейсы репозиториев
│ │ └── unit_of_work.py # Абстрактный Unit of Work
│ ├── infrastructure/
│ │ ├── models/ # ORM-модели SQLAlchemy
│ │ ├── repositories/ # Реализации репозиториев
│ │ └── unit_of_work.py # Конкретный Unit of Work
│ ├── presentation/
│ │ ├── api/ # Роутеры FastAPI
│ │ ├── schemas/ # Pydantic-схемы запросов/ответов
│ │ └── dependencies.py # Зависимости FastAPI
│ ├── rabbit/ # Настройка RabbitMQ, продюсеры
│ ├── workers/ # Воркеры (consumer, outbox dispatcher)
│ ├── config/ # Настройки приложения
│ ├── db/ # Асинхронный движок БД
│ ├── core/ # Вспомогательные модули
│ ├── app.py # Точка входа FastAPI
├── tests/
│ ├── conftest.py
│ ├── e2e/ # End-to-end тесты API
│ └── unit/ # Юнит-тесты сервисов
├── alembic/ # Миграции БД
├── scripts/ # Вспомогательные скрипты
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
* **Poetry**
* **Pytest**
* **Ruff / MyPy / Pre-commit**

---

## 💡 Функциональность

### 💳 Платежи

* `POST /api/v1/payments` – создание платежа
* `GET /api/v1/payments/{payment_id}` – получение информации

### 🔁 Outbox Pattern

При создании платежа транзакционно сохраняется запись в таблице `outbox`. Отдельный воркер `outbox_dispatcher` публикует событие в очередь `payments.new`.

### ⚙️ Consumer

Воркер `payment_consumer` обрабатывает сообщения из очереди, эмулирует платежный шлюз (задержка 2–5 секунд, 90% успех), обновляет статус в БД и отправляет вебхук.

### 🔁 Retry и DLQ

* Повторные попытки при ошибках отправки вебхука (экспоненциальная задержка)
* Необработанные после 3 попыток сообщения попадают в Dead Letter Queue

---

# 🚀 Быстрый старт

## 1. Клонирование репозитория

```bash
git clone https://github.com/Eygenio/Asynchronous_payment_processing_service
```

## 2. Настройка окружения

Скопируйте `.env.template` в `.env` и при необходимости измените параметры:
```bash
cp .env.template .env
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

Запуск тестов:
```bash
pytest
```

---

## 🧹 Проверка кода

```bash
pre-commit run --all-files
ruff check .
ruff format .
mypy src
```

---

## 🔐 Безопасность

* Аутентификация по статическому API-ключу в заголовке `X-API-Key` для всех эндпоинтов `/api/*`
* Пароли и секреты вынесены в `.env`
* База данных и RabbitMQ изолированы внутри Docker-сети

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
Скриншоты работы:
![Снимок экрана от 2026-08-28 12-46-53.png](../../%D0%98%D0%B7%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BA%D0%B8%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%20%D0%BE%D1%82%202026-08-28%2012-46-53.png)
![Снимок экрана от 2026-08-28 12-48-04.png](../../%D0%98%D0%B7%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BA%D0%B8%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%20%D0%BE%D1%82%202026-08-28%2012-48-04.png)
![Снимок экрана от 2026-08-28 12-48-23.png](../../%D0%98%D0%B7%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BA%D0%B8%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%20%D0%BE%D1%82%202026-08-28%2012-48-23.png)
![Снимок экрана от 2026-08-28 12-48-57.png](../../%D0%98%D0%B7%D0%BE%D0%B1%D1%80%D0%B0%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BA%D0%B8%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0/%D0%A1%D0%BD%D0%B8%D0%BC%D0%BE%D0%BA%20%D1%8D%D0%BA%D1%80%D0%B0%D0%BD%D0%B0%20%D0%BE%D1%82%202026-08-28%2012-48-57.png)

---
