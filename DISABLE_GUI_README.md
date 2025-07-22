# NCPA Disable GUI Configuration

This document explains how to use the new `disable_gui` configuration option in NCPA to disable the web GUI while preserving API access.

## Overview

The `disable_gui` configuration option allows you to disable the NCPA web GUI completely while maintaining full API functionality. This is useful for:

- **Headless monitoring setups** where only API access is needed
- **Security-conscious environments** that want to minimize attack surface
- **Automated monitoring systems** that don't require human interaction
- **High-performance environments** where GUI overhead is not desired

## Configuration

### Setting the Option

Add the following line to your `ncpa.cfg` file under the `[listener]` section:

```ini
[listener]
# Disable the web GUI completely while preserving API access
# 0 = Web GUI enabled (default)
# 1 = Web GUI disabled (only API access available)
disable_gui = 1
```

### Default Value

By default, `disable_gui = 0` (GUI enabled), so existing installations will continue to work as before.

## What Gets Disabled

When `disable_gui = 1`, the following endpoints become unavailable:

### Main GUI Routes
- `/` - Main dashboard
- `/gui/` - GUI dashboard
- `/gui/dashboard` - Dashboard page
- `/gui/api` - API browser
- `/gui/stats` - Live statistics
- `/gui/graphs` - Graph generator
- `/gui/checks` - Check history
- `/gui/help` - Help section
- `/gui/top` - Top processes
- `/gui/tail` - Log tailing (Windows)

### Admin GUI Routes
- `/gui/admin` - Admin dashboard
- `/gui/admin/global` - Global settings
- `/gui/admin/listener` - Listener settings
- `/gui/admin/api` - API settings
- `/gui/admin/passive` - Passive monitoring settings
- `/gui/admin/nrdp` - NRDP settings
- `/gui/admin/kafkaproducer` - Kafka producer settings
- `/gui/admin/plugin-directives` - Plugin settings
- `/gui/admin/passive-checks` - Passive checks settings
- `/gui/admin/login` - Admin login

### Supporting Routes
- `/login` - GUI login
- `/logout` - GUI logout
- `/top` - Process monitoring HTML
- `/tail` - Log tailing HTML
- `/graph/*` - Graph generation HTML
- `/update-config/` - Configuration updates via GUI
- `/ws/top` - WebSocket for process monitoring
- `/ws/tail` - WebSocket for log tailing

## What Remains Available

The following endpoints continue to work normally:

### API Endpoints
- `/api/` - API root
- `/api/*` - All API endpoints for monitoring data

### WebSocket API
- `/ws/api/*` - WebSocket API endpoints

### Static Files
- `/static/*` - Static files (CSS, JS, images) - though not useful without GUI

## Example Usage

### 1. Normal Operation (GUI Enabled)
```ini
[listener]
disable_gui = 0
```

Access both GUI and API:
- Web GUI: `https://your-server:5693/`
- API: `https://your-server:5693/api/cpu/percent?token=yourtoken`

### 2. Headless Operation (GUI Disabled)
```ini
[listener]
disable_gui = 1
```

Only API access works:
- Web GUI: `https://your-server:5693/` → "Web GUI is disabled. Only API access is available."
- API: `https://your-server:5693/api/cpu/percent?token=yourtoken` → Works normally

## Testing

A test script is provided to verify the functionality:

```bash
python test_disable_gui.py localhost 5693 mytoken
```

This script will:
1. Test that API endpoints still work
2. Verify that GUI endpoints are properly blocked
3. Report the results

## Security Considerations

### Benefits
- **Reduced attack surface**: GUI endpoints are completely disabled
- **No session management**: No web sessions or cookies are used
- **Token-only authentication**: Only API token authentication is required
- **Simplified deployment**: No need to secure GUI-specific endpoints

### Authentication
When GUI is disabled:
- API endpoints still require valid token authentication
- All GUI routes return an error message regardless of authentication
- WebSocket API endpoints continue to work with token authentication

## Restart Required

After changing the `disable_gui` setting, you must restart the NCPA service for the changes to take effect:

```bash
# Linux/Unix
sudo systemctl restart ncpa
# or
sudo service ncpa restart

# Windows
net stop ncpa
net start ncpa
```

## Troubleshooting

### API Still Not Working
- Verify the API token is correct
- Check that the `community_string` in the `[api]` section is set
- Ensure firewall allows connections to the configured port

### GUI Still Accessible
- Check that `disable_gui = 1` is in the `[listener]` section
- Verify the service was restarted after configuration change
- Check the log files for any configuration errors

### Configuration File Location
The configuration file is typically located at:
- Linux: `/usr/local/ncpa/etc/ncpa.cfg`
- Windows: `C:\Program Files\Nagios\NCPA\etc\ncpa.cfg`

## Compatibility

This feature is compatible with:
- All existing API clients and scripts
- Nagios monitoring checks
- Custom monitoring applications
- Third-party monitoring tools

The feature does not affect:
- API functionality or performance
- Passive monitoring
- Plugin execution
- Log file generation
