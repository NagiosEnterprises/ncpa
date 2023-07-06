"""
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
if len(sys.argv) > 1:
    buildtype = sys.argv[1]

console_colors.set_colors(0x0F) # White on Black
print("Building NCPA for Windows")

# Which python launcher command is available for Windows
python_launcher = 'py' if shutil.which('py') else 'python'

basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
	# subprocess.Popen(['git', 'pull']).wait()
	subprocess.Popen([python_launcher, '-m', 'pip', 'install', '--upgrade', '-r', os.path.join(basedir, 'build', 'resources', 'require.win.txt')]).wait()

# Remove old build
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

console_colors.set_colors(0x09) # Blue on Black
subprocess.Popen([python_launcher, 'setup.py', 'build_exe']).wait()

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
    GIT_LONG = run_cmd("git rev-parse HEAD")
    GIT_SHORT = run_cmd("git rev-parse --short HEAD")
    GIT_UNCOMMITTED = run_cmd("git status --untracked-files=no --porcelain")

    print("GIT_UNCOMMITED:", GIT_UNCOMMITTED)

    if GIT_UNCOMMITTED:
         GIT_LONG = f"{GIT_LONG}++ compiled with uncommitted changes"
         GIT_SHORT = f"{GIT_SHORT}++"

    GIT_HASH_FILE = f"git-{GIT_SHORT}.githash"

    print("GIT_LONG:", GIT_LONG)
    print("GIT_SHORT:", GIT_SHORT)
    print("GIT_HASH_FILE:", GIT_HASH_FILE)

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
ASCII = """
███╗   ██╗ ██████╗██████╗  █████╗
████╗  ██║██╔════╝██╔══██╗██╔══██╗
██╔██╗ ██║██║     ██████╔╝███████║
██║╚██╗██║██║     ██╔═══╝ ██╔══██║
██║ ╚████║╚██████╗██║     ██║  ██║
╚═╝  ╚═══╝ ╚═════╝╚═╝     ╚═╝  ╚═╝
"""
print(ASCII)
print("Build complete!")
print("You can find the installer in the build directory.")

console_colors.reset_colors()