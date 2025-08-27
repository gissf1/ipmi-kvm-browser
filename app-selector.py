#!/usr/bin/env python3
# show a menu to start various UI applications on local X11 server.
# this must be run from within the container

import os
import subprocess
import sys
import stat
import ctypes
from ctypes.util import find_library
import signal

try:
	import tkinter as tk
except ImportError:
	# If tkinter is not found, try to install it. This requires root privileges.
	if os.geteuid() != 0:
		print("FATAL: tkinter is not installed and this script is not running as root.")
		print("Please run as root to install dependencies, or install 'python3-tk' manually.")
		sys.exit(1)

	print("tkinter not found. Attempting to install python3-tk...")
	try:
		# First, update the package list
		subprocess.check_call(["apt-get", "update"])
		# Now, install python3-tk
		subprocess.check_call(["apt-get", "install", "-y", "python3-tk"])

		print("Installation successful. Restarting script...")
		# Re-execute the script to load the new module.
		os.execv(sys.executable, ['python3'] + sys.argv)
	except subprocess.CalledProcessError as e:
		print("FATAL: Failed to install python3-tk. Error: {}".format(e))
		sys.exit(1)
	except FileNotFoundError:
		print("FATAL: 'apt-get' command not found. This script requires a Debian-based system to auto-install dependencies.")
		sys.exit(1)

def check_x11_environment():
	# check if X11 environment variables are set
	if "DISPLAY" not in os.environ:
		raise EnvironmentError("FATAL: DISPLAY environment variable is not set.")

	# check if XAUTHORITY environment variable is set and valid
	# also check if the file exists, is a socket, is readable, and is writable
	xauthority = os.environ.get("XAUTHORITY")
	if not xauthority:
		raise EnvironmentError("FATAL: XAUTHORITY file is not set")
	if not os.path.exists(xauthority):
		raise EnvironmentError("FATAL: XAUTHORITY file does not exist: {}".format(xauthority))
	if not os.access(xauthority, os.R_OK):
		raise EnvironmentError("FATAL: XAUTHORITY file is not readable: {}".format(xauthority))

	# verify that X11 socket is available
	x11_socket = "/tmp/.X11-unix/X0"
	if not os.path.exists(x11_socket):
		raise EnvironmentError("FATAL: X11 socket file does not exist: {}".format(x11_socket))
	if not stat.S_ISSOCK(os.stat(x11_socket).st_mode):
		raise EnvironmentError("FATAL: X11 socket file is not a socket: {}".format(x11_socket))
	if not os.access(x11_socket, os.R_OK):
		raise EnvironmentError("FATAL: X11 socket is not readable: {}".format(x11_socket))
	if not os.access(x11_socket, os.W_OK):
		raise EnvironmentError("FATAL: X11 socket is not writable: {}".format(x11_socket))

def launch_app(command):
	print("Launching app: {}".format(command))
	try:
		# Split the command into a list for Popen
		if isinstance(command, str):
			command = command.split()

		# Launch the application
		process = subprocess.Popen(command)

		# Check if process started successfully
		if process.poll() is not None:
			# Process terminated immediately
			error_msg = "Application failed to start (exit code: {})".format(process.returncode)
			print(error_msg)
			return

		# Set up handler for child process termination
		def handle_sigchld(signum, frame):
			if process.poll() is not None:
				exitcode = process.returncode
				print("Application terminated with exit code: {}".format(exitcode))
				root.quit()
				sys.exit(exitcode)

		signal.signal(signal.SIGCHLD, handle_sigchld)
	except Exception as e:
		error_msg = "Unexpected error at {}: {}".format(
			sys._getframe().f_code.co_name,
			str(e)
		)
		print(error_msg)

def check_binary_exists(binary_name):
	"""Check if a binary exists in the system PATH"""
	try:
		# Use 'which' command to check if binary exists
		# Using subprocess.call for compatibility with older Python versions
		with open(os.devnull, 'w') as devnull:
			result = subprocess.call(['which', binary_name], 
									stdout=devnull, 
									stderr=devnull)
		return result == 0
	except (OSError, FileNotFoundError):
		# Fallback: check common binary locations
		common_paths = ['/usr/bin/', '/bin/', '/usr/local/bin/']
		for path in common_paths:
			full_path = os.path.join(path, binary_name)
			if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
				return True
		return False

class XineramaScreenInfo(ctypes.Structure):
	_fields_ = [
		('screen_number', ctypes.c_int),
		('x_org', ctypes.c_short),
		('y_org', ctypes.c_short),
		('width', ctypes.c_short),
		('height', ctypes.c_short),
	]

def get_monitor_geometries():
	# low-level method of getting xinerama screen geometries using X11 library calls
	global screen_dimensions

	# cache the result to avoid repeated calls
	if 'screen_dimensions' in globals() and screen_dimensions:
		return screen_dimensions

	screen_dimensions = []

	# Find the X11 and Xinerama libraries
	libX11 = find_library('X11')
	libXinerama = find_library('Xinerama')

	if not libX11 or not libXinerama:
		print("Could not find required X11 or Xinerama libraries.")
		exit(1)

	x11 = ctypes.CDLL(libX11)
	xinerama = ctypes.CDLL(libXinerama)

	# Define function prototypes for XineramaQueryScreens
	xinerama.XineramaQueryScreens.argtypes = [
		ctypes.c_void_p,
		ctypes.POINTER(ctypes.c_int)
	]
	xinerama.XineramaQueryScreens.restype = ctypes.POINTER(XineramaScreenInfo)

	# Open X11 display
	display = x11.XOpenDisplay(None)
	if not display:
		raise EnvironmentError("Unable to open X11 display.")

	try:
		# Check if Xinerama is enabled
		if xinerama.XineramaIsActive(display) == 0:
			raise EnvironmentError("Xinerama is not active on this display.")

		# Get screen dimensions
		num_screens = ctypes.c_int()
		screen_info_array = None
		try:
			screen_info_array = xinerama.XineramaQueryScreens(display, ctypes.byref(num_screens))

			if screen_info_array:
				# print("Detected {} Xinerama screens:".format(num_screens.value))
				for i in range(num_screens.value):
					screen = screen_info_array[i]
					# print("Screen {}: x={}, y={}, width={}, height={}".format(i, screen.x_org, screen.y_org, screen.width, screen.height))
					screen_dimensions.append((screen.x_org, screen.y_org, screen.width, screen.height))
		finally:
			# Ensure the memory allocated by Xinerama is always freed
			if screen_info_array:
				x11.XFree(screen_info_array)
	finally:
		# Ensure the display is always closed
		x11.XCloseDisplay(display)

	return screen_dimensions

def get_current_monitor_geometry():
	# determine the geometry of the monitor where the mouse pointer is located
	# assumes a single monitor if Xinerama is not available

	# Get the position of the mouse pointer. This will determine which
	# monitor the window should be centered on.
	pointer_x = root.winfo_pointerx()
	pointer_y = root.winfo_pointery()

	try:
		# Get monitor geometries
		monitors = get_monitor_geometries()
		# Check each monitor to see if the pointer is within its bounds
		for monitor in monitors:
			if (pointer_x >= monitor[0] and pointer_x < monitor[0] + monitor[2] and
				pointer_y >= monitor[1] and pointer_y < monitor[1] + monitor[3]):
				return monitor
	except Exception as e:
		print("Warning: Could not get monitor geometries: {}".format(e))

	# Fallback to full screen dimensions if Xinerama is not available or an error occurs
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()
	return (0, 0, screen_width, screen_height)

def create_ui():
	global root
	root = tk.Tk()
	root.title("Application Launcher")

	apps = [
		("Chromium",   "chromium-browser", "--no-sandbox --disable-sync"),
		("Firefox",    "firefox", None),
		("LXTerminal", "lxterminal", None),
		("XTerm",      "xterm", None),
		("UXTerm",     "uxterm", None),
	]

	last_index = 0
	for i, (name, command, args) in enumerate(apps):
		if not check_binary_exists(command):
			print("Warning: {} binary not found, skipping menu item {}".format(command, name))
			continue
		key = str(last_index + 1)
		print("Using: {} for menu item {}".format(key, name))
		# Format text as "1. Chromium" and set the underline on the hotkey
		button_text = "{}. {}".format(key, name)
		if args:
			cmdline = "{} {}".format(command, args)
		else:
			cmdline = command  # Fixed: was 'app', should be 'command'

		# Fixed lambda syntax and variable capture
		button_callable = lambda cmd=cmdline: launch_app(cmd)
		key_callable = lambda event, cmd=cmdline: launch_app(cmd)

		btn = tk.Button(root, text=button_text, command=button_callable, underline=0)
		btn.pack(fill=tk.X, padx=10, pady=2)
		root.bind(key, key_callable)
		# Add binding for the corresponding numpad key
		root.bind("<KP_{}>".format(key), key_callable)
		last_index += 1

	exit_btn = tk.Button(root, text="Exit (Q or Esc)", command=root.quit, underline=6)
	exit_btn.pack(fill=tk.X, padx=10, pady=15)
	root.bind("<Escape>", lambda event: root.quit())
	root.bind("q", lambda event: root.quit())
	root.bind("Q", lambda event: root.quit())

	# --- Centering Logic ---
	# Force update to get window dimensions
	root.update_idletasks()

	# Get monitor and window dimensions and calculate position
	window_width = root.winfo_reqwidth()
	window_height = root.winfo_reqheight()

	# Get the geometry of the monitor where the mouse pointer is located
	monitor_geometry = get_current_monitor_geometry()

	screen_x = monitor_geometry[0]
	screen_y = monitor_geometry[1]
	screen_width = monitor_geometry[2]
	screen_height = monitor_geometry[3]
	x_coordinate = screen_x + int((screen_width/2) - (window_width/2))
	y_coordinate = screen_y + int((screen_height/2) - (window_height/2))

	# Set position and make window visible
	root.geometry("+{}+{}".format(x_coordinate, y_coordinate))
	root.deiconify() # Show the window

	root.mainloop()

if __name__ == "__main__":
	try:
		check_x11_environment()
		create_ui()
	except Exception as e:
		print(str(e))
		exit(1)