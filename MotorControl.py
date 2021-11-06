from ctypes import *
import time
import os
import sys
import platform
import tempfile
import re
from tkinter import *

# Libximc INSTALLATION
if sys.version_info >= (3, 0):
    import urllib.parse

cur_dir = os.path.abspath(os.path.dirname(__file__))
print(cur_dir)
ximc_dir = os.path.join(cur_dir, "ximc")
ximc_package_dir = os.path.join(
    ximc_dir, "crossplatform", "wrappers", "python")
sys.path.append(ximc_package_dir)  # add ximc.py wrapper to python path

if platform.system() == "Windows":
    arch_dir = "win64" if "64" in platform.architecture()[0] else "win32"
    libdir = os.path.join(ximc_dir, arch_dir)
    os.environ["Path"] = libdir + ";" + os.environ["Path"]  # add dll

try:
    from pyximc import *
except ImportError as err:
    print("Can't import pyximc module. The most probable reason is that you changed the relative location of the testpython.py and pyximc.py files. See developers' documentation for details.")
    exit()
except OSError as err:
    print("Can't load libximc library. Please add all shared libraries to the appropriate places. It is decribed in detail in developers' documentation. On Linux make sure you installed libximc-dev package.\nmake sure that the architecture of the system and the interpreter is the same")
    exit()

# variable 'lib' points to a loaded library
# note that ximc uses stdcall on win
print("Library loaded")

sbuf = create_string_buffer(64)
lib.ximc_version(sbuf)
print("Library version: " + sbuf.raw.decode().rstrip("\0"))

# Set bindy (network) keyfile. Must be called before any call to "enumerate_devices" or "open_device" if you
# wish to use network-attached controllers. Accepts both absolute and relative paths, relative paths are resolved
# relative to the process working directory. If you do not need network devices then "set_bindy_key" is optional.
# In Python make sure to pass byte-array object to this function (b"string literal").
lib.set_bindy_key(os.path.join(ximc_dir, "win32",
                  "keyfile.sqlite").encode("utf-8"))

# This is device search and enumeration with probing. It gives more information about devices.
probe_flags = EnumerateFlags.ENUMERATE_PROBE + EnumerateFlags.ENUMERATE_NETWORK
enum_hints = b"addr=192.168.0.1,172.16.2.3"
# enum_hints = b"addr=" # Use this hint string for broadcast enumerate
devenum = lib.enumerate_devices(probe_flags, enum_hints)
print("Device enum handle: " + repr(devenum))
print("Device enum handle type: " + repr(type(devenum)))

dev_count = lib.get_device_count(devenum)
print("Device count: " + repr(dev_count))

controller_name = controller_name_t()
for dev_ind in range(0, dev_count):
    enum_name = lib.get_device_name(devenum, dev_ind)
    result = lib.get_enumerate_device_controller_name(
        devenum, dev_ind, byref(controller_name))
    if result == Result.Ok:
        print("Enumerated device #{} name (port name): ".format(dev_ind) +
              repr(enum_name) + ". Friendly name: " + repr(controller_name.ControllerName) + ".")

open_name = None
if len(sys.argv) > 1:
    open_name = sys.argv[1]
elif dev_count > 0:
    open_name = lib.get_device_name(devenum, 0)
elif sys.version_info >= (3, 0):
    # use URI for virtual device when there is new urllib python3 API
    tempdir = tempfile.gettempdir() + "/testdevice.bin"
    if os.altsep:
        tempdir = tempdir.replace(os.sep, os.altsep)
    # urlparse build wrong path if scheme is not file
    uri = urllib.parse.urlunparse(urllib.parse.ParseResult(scheme="file",
                                                           netloc=None, path=tempdir, params=None, query=None, fragment=None))
    open_name = re.sub(r'^file', 'xi-emu', uri).encode()

if not open_name:
    exit(1)

if type(open_name) is str:
    open_name = open_name.encode()

print("\nOpen device " + repr(open_name))
device_id = lib.open_device(open_name)
print("Device id: " + repr(device_id))


# ROTATION/CONTROL FUNCTION
def move(lib, device_id, distance, udistance):
    lib.command_move(device_id, distance, udistance)


def homezero(lib, device_id):
    lib.command_homezero(device_id)


def close(lib, device_id):
    lib.close_device(device_id)


def open(lib, device_id):
    lib.open_device(device_id)


def set_speed(lib, device_id, speed):
    mvst = move_settings_t()
    result = lib.get_move_settings(device_id, byref(mvst))
    print("Read command result: " + repr(result))
    print("The speed was equal to {0}. We will change it to {1}".format(
        mvst.Speed, speed))
    mvst.Speed = int(speed)
    result = lib.set_move_settings(device_id, byref(mvst))
    print("Write command result: " + repr(result))


def get_position(lib, device_id):
    x_pos = get_position_t()
    result = lib.get_position(device_id, byref(x_pos))
    print("Result: " + repr(result))
    if result == Result.Ok:
        print("Position: {0} steps, {1} microsteps".format(
            x_pos.Position, x_pos.uPosition))
    return x_pos.Position, x_pos.uPosition
