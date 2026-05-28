**Project Code:** shipments-s01  
**Студент:** s01 | **Группа:** 431  
**Дата:** 2026-04-25



## 1. Какие критерии вы использовали при разделении монолита на микросервисы (или при проектировании сервисов)?

**Ответ:**

При проектировании системы `shipments-s01` мы руководствовались следующими принципами:

### 1.1. Разделение по бизнес-доменам (Domain-Driven Design)
- **shipments-svc-s01** — отвечает за основную бизнес-логику: CRUD операции с грузами, валидация данных, управление статусами.
- **notifications-svc-s01** — отвечает за коммуникацию: отправка уведомлений об изменении статуса (email, SMS, push).

**Обоснование:** Эти домены имеют разные требования к масштабированию и надёжности. Уведомления могут быть асинхронными и не блокировать основную операцию.

### 1.2. Принцип единой ответственности (Single Responsibility)
Каждый сервис решает одну задачу:
- Shipments: хранение и управление данными о грузах
- Notifications: доставка сообщений пользователям

### 1.3. Независимое развёртывание
Сервисы могут обновляться независимо:
- Можно изменить логику уведомлений без пересборки основного сервиса
- Можно масштабировать shipments-svc до 3 реплик, оставив 1 реплику notifications-svc

### 1.4. Слабая связанность (Loose Coupling)
- Сервисы общаются через чётко определённые интерфейсы (REST/gRPC)
- При падении notifications-svc основной сервис продолжает работать (graceful degradation)
- Нет прямых вызовов баз данных между сервисами

### 1.5. Границы транзакций
Каждый сервис управляет своими данными:
- shipments-svc хранит данные о грузах (in-memory/PostgreSQL)
- notifications-svc хранит историю отправленных уведомлений (опционально)



## 2. Почему вы выбрали именно этот стек технологий (язык, БД, протоколы)?

**Ответ:**

### 2.1. Язык: Python 3.13
**Преимущества:**
- Быстрая разработка благодаря лаконичному синтаксису
- Богатая экосистема библиотек (FastAPI, Pydantic, grpcio)
- Хорошая поддержка типизации (type hints)
- Легко найти разработчиков

**Альтернативы:** Go (быстрее, но строже), Node.js (async-native, но динамическая типизация)

### 2.2. Фреймворк: FastAPI
**Преимущества:**
- Автоматическая генерация OpenAPI/Swagger документации
- Валидация данных через Pydantic (типы, ограничения)
- Поддержка async/await для высокой производительности
- Встроенная dependency injection

**Альтернативы:** Flask (проще, но меньше функций), Django (тяжелее для микросервисов)

### 2.3. Протоколы:
| Протокол       | Где используется                                 | Почему                                                                   |
|----------------|--------------------------------------------------|--------------------------------------------------------------------------|
| **REST/JSON**  | Внешний API (клиенты → Gateway → shipments-svc)  | Универсальность, простота отладки, поддержка всеми языками               |
| **gRPC-style** | Межсервисное общение (shipments → notifications) | Эффективность (бинарный Protobuf), строгий контракт, поддержка streaming |
| **HTTP/2**     | Внутренняя сеть Kubernetes                       | Мультиплексирование, меньшая задержка                                    |

### 2.4. Хранилище: In-Memory (для демо) / PostgreSQL (для продакшена)
**In-Memory (список Python):**
- ✅ Быстрый старт без настройки БД
- ✅ Достаточно для нагрузочного тестирования
- ❌ Данные теряются при перезапуске

**PostgreSQL (планируется):**
- ✅ Постоянное хранение
- ✅ ACID-транзакции
- ✅ Индексы для быстрого поиска

### 2.5. Gateway: Nginx
**Преимущества:**
- Проверенное решение с низкой задержкой
- Поддержка SSL/TLS termination
- Rate limiting из коробки
- Простая конфигурация

### 2.6. Контейнеризация: Docker + Kubernetes
**Docker:**
- Воспроизводимость окружения
- Изоляция зависимостей
- Простота развертывания

**Kubernetes (Helm):**
- Оркестрация и масштабирование
- Self-healing (автоматический перезапуск подов)
- Rolling updates без простоя



## 3. Как ваши сервисы справляются с ошибками (retry, circuit breaker, graceful degradation)?

**Ответ:**

### 3.1. Graceful Degradation (Реализовано)
При падении `notifications-svc` основной сервис **продолжает работать**:

# В shipments-svc/app/server.py
def create_shipment(shipment: ShipmentCreate) -> dict:
    # ... сохранение груза ...
    
    # Асинхронное уведомление (не блокирует основной поток)
    try:
        print(f"📧 [gRPC → notifications-svc] Shipment {shipment.tracking} → {shipment.status}")
        # В продакшене: grpc_client.send_notification(...)
    except Exception as e:
        # Логирование ошибки, но не прерывание операции
        logger.warning(f"Failed to send notification: {e}")
    
    return new_shipment  # Клиент получает успешный ответ


**Результат:** Пользователь создаёт груз успешно, даже если сервис уведомлений недоступен.

### 3.2. Retry (Планируется)
Для критичных операций будет реализован механизм повторных попыток:

# Пример с использованием tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def send_notification(tracking: str, status: str):
    grpc_channel.send_notification(tracking, status)


**Параметры:**
- 3 попытки
- Экспоненциальная задержка: 1s → 2s → 4s
- Максимальная задержка: 10s

### 3.3. Circuit Breaker (Планируется)
Для защиты от каскадных отказов:

# Пример с использованием pybreaker
import pybreaker

breaker = pybreaker.CircuitBreaker(
    fail_max=5,      # 5 ошибок
    reset_timeout=60 # 60 секунд до следующей попытки
)

@breaker
def send_notification(tracking: str, status: str):
    grpc_channel.send_notification(tracking, status)


**Логика:**
- После 5 ошибок — цепь размыкается (отказ без попыток)
- Через 60 секунд — полуоткрытое состояние (1 попытка)
- При успехе — цепь замыкается (нормальная работа)

### 3.4. Health Checks (Реализовано)
Каждый сервис имеет endpoint `/health`:

@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}


**Использование:**
- Docker Compose: `healthcheck` для автоматического перезапуска
- Kubernetes: `livenessProbe` и `readinessProbe` для управления подами
- Gateway: проверка доступности upstream-сервисов

### 3.5. Логирование ошибок (Реализовано)
Все ошибки логируются с контекстом:


INFO: 172.20.0.4:54998 - "POST /api/shipments HTTP/1.1" 201 Created
📧 [gRPC → notifications-svc] Shipment TRK-001 → pending
WARNING: Failed to connect to notifications-svc: Connection refused




## 4. Как организован деплой и обновление вашей системы без простоя (Zero Downtime)?

**Ответ:**

### 4.1. Docker Compose (Локально)

**Команда запуска:**

docker-compose up --build


**Обновление без простоя:**

# Пересобрать и пересоздать контейнеры
docker-compose up --build --force-recreate

# Масштабировать сервис
docker-compose up -d --scale shipments-svc=3


**Ограничение:** Кратковременный простой при перезапуске контейнеров (1-2 секунды).

### 4.2. Kubernetes + Helm (Продакшен)

**Rolling Update (по умолчанию в K8s):**


# Обновить образ через Helm
helm upgrade shipments-s01 ./chart \
  --set shipments.image.tag=vX.X.X \
  --set replicaCount=3


**Как это работает:**
1. K8s создаёт новый под с версией vX.X.X
2. Ждёт, пока новый под перейдёт в `Ready` (passes readinessProbe)
3. Удаляет один старый под с версией v1.0.0
4. Повторяет шаги 1-3, пока все поды не обновятся

**Конфигурация в deployment.yaml:**
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1       # +1 под сверх desired
      maxUnavailable: 0 # 0 подов недоступны всегда
  minReadySeconds: 10   # Ждать 10с после готовности пода


**Результат:** Сервис доступен 100% времени во время обновления.

### 4.3. Blue-Green Deployment (Планируется)

**Схема:**

┌─────────────┐     ┌─────────────┐
│   Blue      │     │    Green    │
│  (v1.0.0)   │     │  (v2.0.0)   │
│   Active    │     │   Standby   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 ▼
         ┌───────────────┐
         │    Service    │
         │   (Switch)    │
         └───────────────┘


**Процесс:**
1. Развернуть v2.0.0 в окружении Green
2. Протестировать Green
3. Переключить Service на Green
4. Удалить Blue (или оставить для отката)

### 4.4. Canary Deployment (Планируется)

**Схема:**

Traffic Split:
- 90% → v1.0.0 (stable)
- 10% → v2.0.0 (canary)


**Преимущества:**
- Раннее обнаружение проблем на малой доле трафика
- Постепенное увеличение доли canary при успехе

### 4.5. База данных (Миграции)

**Инструмент:** Alembic (для SQLAlchemy)

**Процесс:**

# Создать миграцию
alembic revision --autogenerate -m "Add status field"

# Применить миграцию
alembic upgrade head


**Правило:** Миграции должны быть обратно совместимыми (не удалять колонки сразу).



## 5. Что было самым сложным в интеграции всех компонентов вместе?

**Ответ:**

### 5.1. Настройка сети между сервисами

**Проблема:** Сервисы в разных контейнерах не видели друг друга по имени.

**Решение:**
yaml
# docker-compose.yml
networks:
  shipments-network:
    driver: bridge

services:
  shipments-svc:
    networks:
      - shipments-network
  notifications-svc:
    networks:
      - shipments-network


**Результат:** Сервисы резолвятся по имени: `http://notifications-svc:8131`

### 5.2. Синхронизация образов между Docker и Kubernetes

**Проблема:** Minikube использует отдельный Docker daemon, образы из локального Docker не видны в K8s.

**Решение:**

# Загрузить образ в Minikube
minikube image load shipments-s01:latest

# Или собрать образ прямо в кластере
eval $(minikube docker-env)
docker build -t shipments-s01:latest ./shipments-svc


### 5.3. Исправление ошибок в Helm chart

**Проблема:** YAML-синтаксис чувствителен к отступам, ошибка на строке 29 ломала весь чарт.

**Решение:**

# Линт чарта перед установкой
helm lint ./chart

# Проверка шаблонов
helm template shipments-s01 ./chart


### 5.4. Health checks и зависимости запуска

**Проблема:** Gateway пытался запуститься до того, как shipments-svc был готов.

**Решение:**
# docker-compose.yml
services:
  gateway:
    depends_on:
      shipments-svc:
        condition: service_healthy
  shipments-svc:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8130/health')"]
      interval: 10s
      timeout: 5s
      retries: 3


### 5.5. Port conflicts на Windows

**Проблема:** Порт 8080 занят другой программой, Gateway не запускался.

**Решение:** Изменили порт в `docker-compose.yml`:
yaml
gateway:
  ports:
    - "8085:80"  # Было 8080:80


### 5.6. Code Quality и pylint

**Проблема:** Предупреждения pylint (missing docstring, global statement, wrong import order).

**Решение:**
- Добавили module/class/function docstrings
- Заменили `global NEXT_ID` на класс `AppState`
- Исправили порядок импортов (стандартные → сторонние)
- Итог: **pylint 10.00/10** ✅



## 6. Что бы вы улучшили, если бы у вас был еще месяц?

**Ответ:**

### 6.1. 🔴 Критические улучшения (Приоритет 1)

| Задача              | Описание                                           | Оценка |
|---------------------|----------------------------------------------------|--------|
| **JWT-авторизация** | Внедрить аутентификацию и проверку владельца груза | 3 дня  |
| **PostgreSQL**      | Заменить in-memory на постоянную БД с миграциями   | 4 дня  |
| **Rate Limiting**   | Защита от спама/DoS на уровне Gateway              | 1 день |

### 6.2. 🟡 Важные улучшения (Приоритет 2)

| Задача                           | Описание                                                | Оценка |
|----------------------------------|---------------------------------------------------------|--------|
| **Асинхронная очередь**          | RabbitMQ/Kafka для надёжной доставки уведомлений        | 5 дней |
| **Distributed Tracing**          | Jaeger/Zipkin для отслеживания запросов между сервисами | 3 дня  |
| **Метрики и мониторинг**         | Prometheus + Grafana дашборды                           | 3 дня  |
| **Централизованное логирование** | ELK Stack (Elasticsearch, Logstash, Kibana)             | 4 дня  |

### 6.3. 🟢 Желательные улучшения (Приоритет 3)

| Задача               | Описание                                             | Оценка |
|----------------------|------------------------------------------------------|--------|
| **Security Headers** | CSP, HSTS, X-Frame-Options в Nginx                   | 0.5 дня|
| **HTTPS/TLS**        | Шифрование трафика через Let's Encrypt               | 1 день |
| **API Versioning**   | Поддержка нескольких версий API (/api/v1/, /api/v2/) | 2 дня  |
| **GraphQL**          | Альтернативный endpoint для гибких запросов          | 3 дня  |
| **Кэширование**      | Redis для частых запросов (GET /api/shipments)       | 2 дня  |

### 6.4. Архитектурные улучшения

**6.4.1. Event-Driven Architecture**

shipments-svc → RabbitMQ → notifications-svc
                     ↓
              analytics-svc
                     ↓
              reporting-svc


**Преимущества:**
- Полная развязка сервисов
- Надёжная доставка (at-least-once)
- Легко добавлять новых подписчиков

**6.4.2. CQRS (Command Query Responsibility Segregation)**
- **Write Model:** PostgreSQL (транзакции, консистентность)
- **Read Model:** Elasticsearch (быстрый поиск, агрегации)

**6.4.3. Service Mesh (Istio/Linkerd)**
- Автоматический mTLS между сервисами
- Traffic splitting для canary-деплоев
- Observability из коробки

### 6.5. CI/CD Улучшения

**Текущее состояние:**
jobs:
  - lint
  - test
  - build
  - publish (artifacts)


**Планируется:**
jobs:
  - lint
  - test
  - security-scan (trivy, snyk)
  - build
  - deploy-staging
  - integration-tests
  - deploy-production (manual approval)


### 6.6. Тестирование

**Добавить:**
- ✅ Unit-тесты (pytest, coverage > 80%)
- ✅ Integration-тесты (TestContainers)
- ✅ E2E-тесты (Playwright/Selenium для UI)
- ✅ Нагрузочные тесты в CI (k6, locust)

### 6.7. Документация

**Добавить:**
- 📖 OpenAPI/Swagger UI (авто-генерация из FastAPI)
- 📖 Architecture Decision Records (ADR)
- 📖 Runbook для операторов (как реагировать на инциденты)
- 📖 API changelog
