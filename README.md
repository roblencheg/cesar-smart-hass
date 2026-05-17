# Cesar Smart ReadOnly for Home Assistant

[![GitHub Release](https://img.shields.io/github/v/release/roblencheg/cesar-smart-hass)](https://github.com/roblencheg/cesar-smart-hass/releases)
[![HACS Validation](https://github.com/roblencheg/cesar-smart-hass/actions/workflows/validate.yml/badge.svg)](https://github.com/roblencheg/cesar-smart-hass/actions/workflows/validate.yml)

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roblencheg&repository=cesar-smart-hass&category=integration)
[![Open your Home Assistant instance and start configuring the Cesar Smart ReadOnly integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=cesar_smart)

**Read-only** Home Assistant integration for Cesar Smart vehicle security system (Haval, Great Wall, etc.).

> ⚠️ **Read-Only Notice**: This integration is strictly read-only. It **cannot** send any commands to your vehicle (lock/unlock, remote start, horn, etc.). It only reads vehicle status, location, and receives real-time events.

---

## Features

- Vehicle status monitoring (engine, doors, temperature, fuel, mileage, battery, etc.)
- GPS location tracking
- Optional WebSocket real-time updates
- Configurable polling intervals
- Multi-language support (English, Russian)
- Privacy-focused: sensitive data is redacted in diagnostics
- SIM Balance monitoring (disabled by default)

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations" → "Custom repositories"
3. Add `https://github.com/roblencheg/cesar-smart-hass` as a custom repository of type "Integration"
4. Click "Download" on the "Cesar Smart ReadOnly" integration
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/cesar_smart/` directory to your Home Assistant `custom_components/` directory
2. Restart Home Assistant

## Setup

1. Go to Settings → Devices & Services → Add Integration
2. Search for "Cesar Smart ReadOnly"
3. Enter your Cesar Smart account credentials
4. Select your vehicle if multiple are found
5. Configure optional settings (WebSocket, polling intervals)

> No YAML configuration required.

## Entities

### Sensors
- Engine State, Security Mode, Fuel Level, Mileage, Battery Voltage
- Engine Temperature, Cabin Temperature, Outdoor Temperature
- Left/Right Side Temperature (disabled by default)
- Label, Last Update
- Location Speed, Location Course (course disabled by default)
- SIM Balance (disabled by default) — value, currency, last updated

### Binary Sensors
- Ignition, Hood, Doors (4x), Trunk, Engine Running
- Remote Start by Phone (disabled by default)

### Device Tracker
- GPS location with speed and course attributes

## SIM Balance Troubleshooting

If the SIM Balance sensor shows `unknown`:

1. Enable `debug_attributes` in integration options
2. Call `cesar_smart.force_refresh` with `include_balance: true`
3. If still unknown, call `cesar_smart.balance_probe` which directly invokes the balance endpoint and writes diagnostic info to the Home Assistant log
4. Check the logs for lines starting with:
   - `SIM balance raw response keys=`
   - `extracted value=`
   - `currency=`

The `balance_probe` service immediately queries the balance API and updates the sensor data, even outside the normal polling schedule.

---

## Known Limitations

- This is an **unofficial** integration using the Cesar Smart mobile API
- Cloud polling may have delays
- WebSocket connection may be unstable (falls back to polling)
- Command/control features are intentionally omitted
- Some vehicle status fields may be model-specific

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Lint
ruff check custom_components/cesar_smart/
```

## Credits

Icon based on OpenMoji "green salad" (U+1F957), licensed under CC BY-SA 4.0.

## License

MIT License

---

# Cesar Smart ReadOnly для Home Assistant

**Только чтение.** Интеграция Home Assistant для системы охраны Cesar Smart (Haval, Great Wall и др.).

> ⚠️ Интеграция работает только на чтение. Она **не может** отправлять команды автомобилю (lock/unlock, remote start, horn и т.д.). Только чтение статусов, местоположения и событий в реальном времени.

## Возможности

- Мониторинг статусов (двигатель, двери, температура, топливо, пробег, АКБ и др.)
- Отслеживание GPS-местоположения
- Опциональные WebSocket-обновления в реальном времени
- Настраиваемые интервалы опроса
- Поддержка русского и английского языков
- Конфиденциальность: чувствительные данные скрыты в диагностике
- Мониторинг баланса SIM-карты (отключено по умолчанию)

## Установка

### HACS (рекомендуется)

1. Откройте HACS в Home Assistant
2. Перейдите "Интеграции" → "Пользовательские репозитории"
3. Добавьте `https://github.com/roblencheg/cesar-smart-hass` как пользовательский репозиторий типа "Интеграция"
4. Нажмите "Загрузить" на карточке "Cesar Smart ReadOnly"
5. Перезагрузите Home Assistant

### Вручную

1. Скопируйте каталог `custom_components/cesar_smart/` в `custom_components/` вашего Home Assistant
2. Перезагрузите Home Assistant

## Настройка

1. Перейдите Настройки → Устройства и службы → Добавить интеграцию
2. Найдите "Cesar Smart ReadOnly"
3. Введите логин и пароль от Cesar Smart
4. Выберите автомобиль (если их несколько)
5. Настройте опциональные параметры (WebSocket, интервалы опроса)

> Конфигурация через YAML не требуется.
