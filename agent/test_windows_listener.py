import ncpa_windows

__test__ = False
listener = ncpa_windows.Listener(debug=True)
listener.Initialize(None)
listener.start()
