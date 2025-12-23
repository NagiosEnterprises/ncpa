from __future__ import print_function
"""
Builds the Windows installer for NCPA.

Called from build_windows.bat
 -sys.argv[1] = path to python.exe to use
 -sys.argv[2] = build type (release or nightly)
"""
""" OLD, TODO: replace
Builds the Windows installer for NCPA.

Run as Administrator on Windows
-pip installs prereqs to the python interpreter that is running this script
-cx_Freeze builds the executable
-NSIS builds the installer
"""

import os
import shutil
import subprocess
import sys

import ctypes, struct

class ConsoleColors:
    STD_OUTPUT_HANDLE = -11

    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.hstdout = self.kernel32.GetStdHandle(self.STD_OUTPUT_HANDLE)
        self.get_console_screen_buffer_info()

    def get_console_screen_buffer_info(self):
        csbi = ctypes.create_string_buffer(22)
        self.kernel32.GetConsoleScreenBufferInfo(self.hstdout, csbi)
        (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
        self.original_colors = wattr

    def set_colors(self, color_attributes):
        self.kernel32.SetConsoleTextAttribute(self.hstdout, color_attributes)

    def reset_colors(self):
        self.set_colors(self.original_colors)

console_colors = ConsoleColors()

# --------------------------
# Configuration/Setup
# --------------------------

# Grab command line arguments
buildtype = 'release'
buildtype = 'nightly'
if len(sys.argv) > 2:
    buildtype = sys.argv[2]

console_colors.set_colors(0x0F) # White on Black
print("Building NCPA for Windows")

for arg in sys.argv:
    print("arg:", arg)

# Which python launcher command is available for Windows
python_launcher = sys.argv[1] # TODO: remove this old: 'py' if shutil.which('py') else 'python'
python_launcher = '/'.join(python_launcher.split('\\'))
print("python_launcher:", python_launcher)

# Set up paths
# basedir = \ncpa\
basedir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
nsi_store = os.path.join(basedir, 'build', 'resources', 'ncpa.nsi')
print("nsi_store:", nsi_store)

nsi = os.path.join(basedir, 'agent', 'build', 'ncpa.nsi')
nsis = os.path.join(os.environ['PROGRAMFILES(X86)'] if 'PROGRAMFILES(X86)' in os.environ else os.environ['PROGRAMFILES'], 'NSIS', 'makensis.exe')

os.chdir(basedir)

with open('VERSION') as version_file:
    version = version_file.readline().strip()

try:
    os.remove(os.path.join(basedir, 'build', 'ncpa-%s.exe' % version))
except:
    pass

# Building nightly versions requires a git pull and pip upgrade
if buildtype == 'nightly':
    print("Looking for list of pip packages to install in %s" % os.path.join(basedir, 'build', 'resources', 'require.win.txt'))
    # subprocess.Popen(['git', 'pull']).wait()
    
    # Check if we're in a virtual environment (Python 3.3+)
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print("Using virtual environment for package installation")
        # In a virtual environment, use pip directly
        subprocess.Popen([python_launcher, '-m', 'pip', 'install', '--upgrade', 'pip']).wait()
        subprocess.Popen([python_launcher, '-m', 'pip', 'install', '--upgrade', '-r', os.path.join(basedir, 'build', 'resources', 'require.win.txt')]).wait()
    else:
        print("Using system Python for package installation")
        # For system Python, use the original method
        subprocess.Popen([python_launcher, '-m', 'pip', 'install', '--upgrade', 'pip']).wait()
        subprocess.Popen([python_launcher, '-m', 'pip', 'install', '--upgrade', '-r', os.path.join(basedir, 'build', 'resources', 'require.win.txt')]).wait()

# Remove old build
print("Removing old build")
subprocess.Popen(['rmdir', os.path.join(basedir, 'agent', 'build'), '/s', '/q'], shell=True).wait()

os.chdir('agent')
if not os.path.exists('var'):
    os.mkdir('var')
if not os.path.exists('plugins'):
    os.mkdir('plugins')
if not os.path.exists('build'):
    os.mkdir('build')

sys.path.append(os.getcwd())

# --------------------------
# build with cx_Freeze
# --------------------------

console_colors.set_colors(0x0B) # Lighter Blue on Black
print("Freezing with cx_Freeze")
# print("you can track progress in ncpa\\build\\cxFreeze_build.log")
# print("Python launcher:", python_launcher)
## opt 1: run in console:
subprocess.Popen([python_launcher, 'setup.py', 'build_exe']).wait() # TODO: determine if we can/should update this to build instead of build_exe
## opt 2: run with logging:
# with open(os.path.join(basedir, 'build', 'cxFreeze_build.log'), 'w') as logfile:
#     subprocess.Popen([python_launcher, 'setup.py', 'build_exe'], stdout=logfile).wait()
print("Done freezing")

# --------------------------
# save git hash to file
# --------------------------

GIT_LONG = "Not built under GIT"
GIT_HASH_FILE = "NoGIT.githash"

def run_cmd(cmd):
     process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
     output, error = process.communicate()
     return output.strip().decode()

console_colors.set_colors(0x0A) # Green on Black
try:
    GIT_LONG        = run_cmd("git rev-parse HEAD")
    GIT_SHORT       = run_cmd("git rev-parse --short HEAD")
    GIT_UNCOMMITTED = run_cmd("git status --untracked-files=no --porcelain")

    print("GIT_UNCOMMITTED:\n", GIT_UNCOMMITTED)

    if GIT_UNCOMMITTED:
         GIT_LONG  = f"{GIT_LONG}++ compiled with uncommitted changes"
         GIT_SHORT = f"{GIT_SHORT}++"

    GIT_HASH_FILE = f"git-{GIT_SHORT}.githash"

    print("GIT_LONG:"       , GIT_LONG)
    print("GIT_SHORT:"      , GIT_SHORT)
    print("GIT_HASH_FILE:"  , GIT_HASH_FILE)

except:
    console_colors.set_colors(0x0C) # Red on Black
    print("GIT_LONG:", GIT_LONG)
    print("GIT_SHORT:", GIT_SHORT)

with open(os.path.join(basedir, 'agent', 'build', 'NCPA', GIT_HASH_FILE), 'w') as f:
    f.write(GIT_LONG)

# --------------------------
# build NSIS installer and copy to build directory
# --------------------------

console_colors.set_colors(0x0F) # White on Black
environ = os.environ.copy()
environ['NCPA_BUILD_VER'] = version
if not version[-1].isdigit():
    x = version.rsplit('.', 1)
    environ['NCPA_BUILD_VER_CLEAN'] = x[0]
else:
    environ['NCPA_BUILD_VER_CLEAN'] = version
shutil.copy(nsi_store, nsi)
b = subprocess.Popen([nsis, nsi], env=environ)
b.wait()

shutil.copyfile(os.path.join(basedir, 'agent', 'build', 'ncpa-%s.exe' % version),
                os.path.join(basedir, 'build', 'ncpa-%s.exe' % version))

console_colors.set_colors(0x0A) # Green on Black

# ASCII = """
#   _   _  ____ ____   _      _           _ _     _                             _      _       _
#  | \ | |/ ___|  _ \ / \    | |__  _   _(_) | __| |   ___ ___  _ __ ___  _ __ | | ___| |_ ___| |
#  |  \| | |   | |_) / _ \   | '_ \| | | | | |/ _` |  / __/ _ \| '_ ` _ \| '_ \| |/ _ \ __/ _ \ |
#  | |\  | |___|  __/ ___ \  | |_) | |_| | | | (_| | | (_| (_) | | | | | | |_) | |  __/ ||  __/_|
#  |_| \_|\____|_| /_/   \_\ |_.__/ \__,_|_|_|\__,_|  \___\___/|_| |_| |_| .__/|_|\___|\__\___(_)
#                                                                        |_|
# """
# print(ASCII)

print("NCPA %s build complete" % version)
print("You can find the installer in the ncpa\\build directory.")

console_colors.reset_colors()