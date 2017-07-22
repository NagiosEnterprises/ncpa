import ncpa_windows
import sys

__test__ = False

# Grab command line arguments
opt = sys.argv[1]

if opt == 'listener' or opt == None:
	listener = ncpa_windows.Listener(debug=True)
	listener.Initialize(None)
	listener.start()
elif opt == 'passive':
	passive = ncpa_windows.Passive(debug=True)
	passive.Initialize(None)
	passive.start()
