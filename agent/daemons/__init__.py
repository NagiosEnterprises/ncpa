import platform
import abstract

if not platform.system() == "Windows":
    import posix
else:
    import windows
