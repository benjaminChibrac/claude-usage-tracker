# Claude Usage Tracker - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Home Assistant custom integration for monitoring Claude Code usage metrics in real-time.

## Features

- 10 sensor entities tracking session and weekly usage
- Real-time cost monitoring with customizable refresh intervals
- UI-based configuration (no YAML required)
- Support for API key authentication
- Automatic updates via HACS

## Prerequisites

- Home Assistant 2023.1 or newer
- Claude Usage API running and accessible from Home Assistant
  - See [api/README.md](../../api/README.md) for API setup

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/benjaminChibrac/claude-usage-tracker`
6. Category: "Integration"
7. Click "Add"
8. Click "Install" on the Claude Usage Tracker card
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/claude_usage` directory from this repository
2. Copy it to `<config_dir>/custom_components/claude_usage` in your Home Assistant installation
3. Restart Home Assistant

## Configuration

1. Navigate to **Settings** > **Devices & Services**
2. Click **Add Integration**
3. Search for "Claude Usage Tracker"
4. Enter your API details:
   - **Host**: IP address or hostname of the API server (e.g., `192.168.1.100`)
   - **Port**: API port (default: `8383`)
   - **API Key**: Optional, if configured in the API
   - **Use SSL**: Enable if using HTTPS

5. Click **Submit**

### Options

After setup, you can configure:
- **Update interval**: How often to fetch data (30-3600 seconds, default: 60)

Access options via: **Settings** > **Devices & Services** > **Claude Usage Tracker** > **Configure**

## Available Sensors

### Session Sensors

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.claude_usage_session_used` | Session Used | USD | Current session cost |
| `sensor.claude_usage_session_limit` | Session Limit | USD | Session cost limit |
| `sensor.claude_usage_session_percentage` | Session Usage | % | Percentage of session limit used |
| `sensor.claude_usage_session_remaining` | Session Remaining | USD | Remaining session budget |
| `sensor.claude_usage_session_active` | Session Active | - | Session status (active/inactive) |
| `sensor.claude_usage_session_burn_rate` | Session Burn Rate | USD/h | Current spending rate per hour |

### Weekly Sensors

| Entity ID | Name | Unit | Description |
|-----------|------|------|-------------|
| `sensor.claude_usage_weekly_used` | Weekly Used | USD | Current week total cost |
| `sensor.claude_usage_weekly_limit` | Weekly Limit | USD | Weekly cost limit |
| `sensor.claude_usage_weekly_percentage` | Weekly Usage | % | Percentage of weekly limit used |
| `sensor.claude_usage_weekly_remaining` | Weekly Remaining | USD | Remaining weekly budget |

### Sensor Attributes

**Session Used** includes:
- `started_at`: Session start timestamp
- `ends_at`: Session end timestamp
- `projection_total_cost`: Projected total cost at end

**Weekly Used** includes:
- `week_start`: Week start date

## Dashboard Example

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Claude Usage - Session
    entities:
      - entity: sensor.claude_usage_session_percentage
        name: Usage
      - entity: sensor.claude_usage_session_used
        name: Used
      - entity: sensor.claude_usage_session_remaining
        name: Remaining
      - entity: sensor.claude_usage_session_burn_rate
        name: Burn Rate
      - entity: sensor.claude_usage_session_active
        name: Status

  - type: entities
    title: Claude Usage - Weekly
    entities:
      - entity: sensor.claude_usage_weekly_percentage
        name: Usage
      - entity: sensor.claude_usage_weekly_used
        name: Used
      - entity: sensor.claude_usage_weekly_remaining
        name: Remaining

  - type: gauge
    entity: sensor.claude_usage_session_percentage
    min: 0
    max: 100
    name: Session Usage
    severity:
      green: 0
      yellow: 70
      red: 90

  - type: gauge
    entity: sensor.claude_usage_weekly_percentage
    min: 0
    max: 100
    name: Weekly Usage
    severity:
      green: 0
      yellow: 70
      red: 90
```

## Automation Example

Alert when weekly usage exceeds 80%:

```yaml
automation:
  - alias: "Claude Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.claude_usage_weekly_percentage
        above: 80
    action:
      - service: notify.mobile_app
        data:
          title: "Claude Usage Alert"
          message: "Weekly usage is at {{ states('sensor.claude_usage_weekly_percentage') }}%"
```

## Troubleshooting

### Integration not appearing in setup

1. Verify files are in `<config_dir>/custom_components/claude_usage/`
2. Check Home Assistant logs for errors
3. Restart Home Assistant

### Sensors showing "Unavailable"

1. Verify API is running and accessible:
   ```bash
   curl http://<api-host>:<api-port>/health
   ```
2. Check API logs:
   ```bash
   docker logs claude-usage-api
   ```
3. Verify API key if configured
4. Check Home Assistant logs for connection errors

### Update interval not changing

1. Go to **Settings** > **Devices & Services**
2. Click **Configure** on Claude Usage Tracker
3. Change update interval
4. Click **Submit**
5. Wait for next update cycle

## Support

- **Issues**: https://github.com/benjaminChibrac/claude-usage-tracker/issues
- **API Documentation**: [api/README.md](../../api/README.md)

## License

See repository LICENSE file.
