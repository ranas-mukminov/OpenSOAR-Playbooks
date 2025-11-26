# OpenSOAR Playbooks

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![run-as-daemon.ru](https://img.shields.io/badge/by-run--as--daemon.ru-orange)](https://run-as-daemon.ru)

**Open-source движок SOAR-плейбуков для автоматизации реагирования на инциденты**

OpenSOAR Playbooks — это production-ready платформа для автоматизации реагирования на инциденты безопасности (SOAR). Система позволяет описывать сложные процессы реагирования в виде YAML-плейбуков и автоматизировать их выполнение.

🔗 **Сайт**: [run-as-daemon.ru](https://run-as-daemon.ru)  
👤 **Автор**: [@ranas-mukminov](https://github.com/ranas-mukminov)

---

## Возможности

✅ **YAML DSL для плейбуков** - описание сложных сценариев без программирования  
✅ **Движок выполнения** - асинхронное выполнение с паузой/возобновлением  
✅ **Фреймворк коннекторов** - подключаемые интеграции (firewall, ticketing, email, Slack и др.)  
✅ **Участие человека** - шаги ручного подтверждения в автоматических процессах  
✅ **Условная логика** - ветвление на основе данных инцидента или предыдущих шагов  
✅ **REST API** - полноценный FastAPI бэкенд для управления плейбуками и инцидентами  
✅ **Шаблоны Jinja2** - динамический доступ к данным через `{{ incident.severity }}`  
✅ **Production готовность** - PostgreSQL хранилище, структурированные логи, комплексные тесты  

---

## Быстрый старт

### Требования

- Python 3.11+
- PostgreSQL 14+
- Виртуальное окружение (venv, virtualenv)

### Установка

```bash
# Клонировать репозиторий
git clone https://github.com/ranas-mukminov/OpenSOAR-Playbooks.git
cd OpenSOAR-Playbooks

# Создать виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установить зависимости
pip install -e ".[dev]"

# Настроить окружение
cp .env.example .env
# Отредактировать .env с вашими данными БД

# Инициализировать базу данных
alembic upgrade head

# Запустить API сервер
uvicorn app.main:app --reload
```

API доступен по адресу `http://localhost:8000`

Интерактивная документация: `http://localhost:8000/docs`

### Запуск тестов

```bash
pytest
```

---

## Примеры использования

### 1. Загрузка плейбука

```bash
curl -X POST http://localhost:8000/playbooks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-this" \
  -d @examples/playbooks/block_ip_and_ticket.yaml
```

### 2. Создание инцидента

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-this" \
  -d '{
    "title": "Обнаружен вредоносный IP",
    "severity": "high",
    "payload": {
      "src_ip": "192.0.2.1",
      "dest_port": 22
    },
    "tags": ["malicious_ip", "ssh_bruteforce"]
  }'
```

### 3. Запуск плейбука

```bash
curl -X POST http://localhost:8000/playbooks/1/run \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key-change-this" \
  -d '{"incident_id": 1}'
```

### 4. Проверка статуса выполнения

```bash
curl http://localhost:8000/runs/1 \
  -H "X-API-Key: your-secret-api-key-change-this"
```

---

## Документация

- [Архитектура системы](docs/architecture.md)
- [Справочник по DSL плейбуков](docs/playbook_dsl.md)
- [Руководство по разработке коннекторов](docs/connector_development.md)

---

## Примеры плейбуков

См. [examples/playbooks/](examples/playbooks/) для полных примеров:

- **block_ip_and_ticket.yaml** - блокировка вредоносного IP и создание тикета
- **suspend_user_with_approval.yaml** - блокировка учётной записи с ручным подтверждением
- **phishing_email_response.yaml** - автоматическое реагирование на фишинговые письма

---

## Коммерческая поддержка

**Профессиональные услуги от [run-as-daemon.ru](https://run-as-daemon.ru):**

- ✅ Внедрение и настройка SOAR платформы
- ✅ Разработка собственных коннекторов для специфичных систем
- ✅ Аудит инфраструктуры и консалтинг по автоматизации безопасности
- ✅ Поддержка DevOps / SRE и настройка мониторинга
- ✅ Резервное копирование и планирование аварийного восстановления

**Контакт**: [run-as-daemon.ru](https://run-as-daemon.ru)

---

## Структура проекта

```
opensoar-playbooks/
├── app/
│   ├── api/              # FastAPI роуты
│   ├── core/             # Бизнес-логика, движок, коннекторы
│   └── db/               # Модели БД и миграции
├── tests/                # Тесты
├── examples/playbooks/   # Примеры YAML плейбуков
└── docs/                 # Документация
```

---

## Внесение вклада

Приветствуются любые вклады! См. [CONTRIBUTING.md](CONTRIBUTING.md) для рекомендаций.

---

## Лицензия

Apache License 2.0 - см. файл [LICENSE](LICENSE)

---

## Приватность и соответствие требованиям

Инструмент по умолчанию не собирает телеметрию или персональные данные. Все обрабатываемые данные остаются в вашей инфраструктуре.

При продакшн-внедрении с обработкой персональных данных обеспечьте соответствие:
- GDPR (Общий регламент по защите данных ЕС)
- 152-ФЗ (Федеральный закон о персональных данных РФ)
- Другим применимым местным регуляциям по защите данных

---

**Создано с ❤️ [@ranas-mukminov](https://github.com/ranas-mukminov) | [run-as-daemon.ru](https://run-as-daemon.ru)**
