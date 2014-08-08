1.8.0
==================
- Added graphing frontend, available via /graph-picker.html

1.7.1
==================
- Fixed issue with SSL certificates using the same serial number
- Fixed threading error on NCPA listener start/stop
- Added backwards compatability with the api/service(s) call to work with old plugins/checks
- Plugin/file type directives now retain quotes around $plugin_name when being passed to the command line
- Fixed Windows logging issue where logs were not at var/*.log
- Added log rotation to all clients, logs rotate at 20MB and will rotate once before overwriting old logs
- Changed log format to be more descriptive
- Changed test runner to be Python rather than sh to run tests on Windows
- Added safeguards when importing disk nodes that prevented the listener from starting in certain circumstances
- diskperf -Y is now automatically run during Windows install
- Added link to the /top service in the UI

1.7.0 - 07/29/2014
==================
- Updated help documentation to include changes in 1.7.0
- Fixed init script for listener not getting the PID file correctly
- Fixed build issue with cx_Freeze which caused the built agent to not run
- Fixed build issue with docs not building during build process
- Fixed dependency issues with Debian systems
- Fixed doc builds during compilation
- Moved away from the Flask development server for serving HTTPS requests
- Now manually creating SSL certificates, and added ability to specify
  cert and key files by specifying in the certificate field by
  a comma-delimited [path/to/cert],[path/to/key]
- Added full tests for NRDP
- Moved to non-blocking system using gevent to accomodate many connections
- Added realtime graphs
- Added Windows Event Log monitoring
- Added Windows counters monitoring ability

1.6.1
==================
- Fixed passive check settings being set during install

1.6.0
==================
- Updated build and versioning process

1.5.0
==================
- Rebuilt build system for NCPA
- Fixed NRDS issue where configs were getting overwritten
- Fixed Issue Where NRDS would not connect to NRDS server
- Added ability to specify SSL certificate by giving path to cert, path to pem
- TODO: Fix Windows issue where plugins would only run once
