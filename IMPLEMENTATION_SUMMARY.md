# NCPA Disable GUI Feature - Implementation Summary

## Overview
This implementation adds a new configuration option `disable_gui` to NCPA that allows disabling the web GUI while preserving full API functionality.

## Changes Made

### 1. Configuration Option Added
**File:** `agent/ncpa.py`
- Added `'disable_gui': '0'` to the `cfg_defaults['listener']` section
- Default value is '0' (GUI enabled) for backward compatibility

### 2. GUI Disable Decorator
**File:** `agent/listener/server.py`
- Added `gui_enabled_required()` decorator function
- Checks if `disable_gui` is set to '1' and returns error message if GUI is disabled
- Returns: "Web GUI is disabled. Only API access is available."

### 3. Protected Routes
Applied `@gui_enabled_required` decorator to all GUI-related routes:

#### Main GUI Routes:
- `/` - Main dashboard redirect
- `/gui/` - GUI dashboard
- `/gui/checks` - Check history
- `/gui/stats` - Live statistics
- `/gui/top` - Top processes view
- `/gui/tail` - Log tailing view
- `/gui/graphs` - Graph generator
- `/gui/api` - API browser
- `/gui/help` - Help section

#### Admin GUI Routes:
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
- `/gui/admin/clear-check-log` - Clear check log

#### Supporting Routes:
- `/login` - GUI login
- `/logout` - GUI logout
- `/top` - Process monitoring HTML
- `/tail` - Log tailing HTML
- `/graph/<path:accessor>` - Graph generation HTML
- `/update-config/` - Configuration updates via GUI
- `/ws/top` - WebSocket for process monitoring
- `/ws/tail` - WebSocket for log tailing

### 4. API Routes (Unchanged)
These routes are NOT affected and continue to work normally:
- `/api/` - API root
- `/api/<path:accessor>` - All API endpoints
- `/ws/api/<path:accessor>` - WebSocket API endpoints

### 5. Documentation Updates
**File:** `agent/etc/ncpa.cfg`
- Added documentation for the new `disable_gui` option
- Explains purpose and usage

**File:** `agent/etc/ncpa.cfg.sample`
- Added commented example of the `disable_gui` option

### 6. Additional Files Created
- `test_disable_gui.py` - Test script to verify functionality
- `DISABLE_GUI_README.md` - Comprehensive documentation
- `ncpa-headless-example.cfg` - Example configuration for headless setup

## Configuration Usage

### Enable GUI (Default)
```ini
[listener]
disable_gui = 0
```

### Disable GUI (API-only)
```ini
[listener]
disable_gui = 1
```

## Security Benefits

1. **Reduced Attack Surface**: GUI endpoints are completely disabled
2. **No Session Management**: No web sessions or cookies when GUI is disabled
3. **Token-only Authentication**: Only API token authentication is required
4. **Simplified Deployment**: No need to secure GUI-specific endpoints

## Testing

The implementation can be tested using:
```bash
python test_disable_gui.py localhost 5693 mytoken
```

This verifies:
- API endpoints still work
- GUI endpoints are properly blocked
- Appropriate error messages are returned

## Backward Compatibility

- Default value is '0' (GUI enabled)
- Existing installations continue to work unchanged
- No breaking changes to API functionality
- All existing API clients and monitoring tools remain compatible

## Implementation Details

### Error Handling
- GUI routes return a user-friendly error message when disabled
- API routes are completely unaffected
- WebSocket API endpoints continue to work normally

### Performance
- No performance impact on API endpoints
- GUI routes are blocked early in the request processing
- Minimal overhead when GUI is disabled

### Security
- GUI disable check happens after authentication decorators
- API token authentication still required for API endpoints
- No bypass mechanisms for disabled GUI routes

## Future Enhancements

Potential future improvements:
1. Runtime configuration change (without restart)
2. Selective GUI component disabling
3. Custom error pages for disabled GUI
4. Integration with existing admin_gui_access setting

## Files Modified

1. `/home/bbahner/ncpa/agent/ncpa.py` - Added configuration default
2. `/home/bbahner/ncpa/agent/listener/server.py` - Added decorator and applied to routes
3. `/home/bbahner/ncpa/agent/etc/ncpa.cfg` - Added documentation
4. `/home/bbahner/ncpa/agent/etc/ncpa.cfg.sample` - Added example

## Files Created

1. `/home/bbahner/ncpa/test_disable_gui.py` - Test script
2. `/home/bbahner/ncpa/DISABLE_GUI_README.md` - Documentation
3. `/home/bbahner/ncpa/ncpa-headless-example.cfg` - Example configuration
