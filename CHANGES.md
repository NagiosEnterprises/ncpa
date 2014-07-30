1.7.0 - ??/??/2014
====================
- Updated help documentation to include changes in 1.7.0
- Fixed init script for listener not getting the PID file correctly
- Fixed build issue with cx_Freeze which caused the built agent to not run
- Fixed build issue with docs not building during build process
- Fixed issue with SSL certificates using the same serial number
- Fixed dependency issues with Debian systems
- Fixed doc builds during compilation
- Moved away from the Flask development server for serving HTTPS requests
- Now manually creating SSL certificates, and added ability to specify
  cert and key files by specifying in the certificate field by
  a comma-delimited [path/to/cert],[path/to/key]

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
