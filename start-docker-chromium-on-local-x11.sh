#!/bin/bash
# Start a Docker container running Chromium browser on local X11 server
# The container:
# - runs as current user
# - uses private directory under via-x11/ for .config
# - uses local X11 socket and Xauthority file for authentication

if [ -z "$DISPLAY" ]; then
	echo "FATAL: DISPLAY environment variable is not set." >&2
	exit 1
fi

MYDIR=$( dirname "$( realpath "$0" )" )

if [ ! -d "$MYDIR/via-x11" ]; then
	echo "FATAL: unable to find via-x11 path: $MYDIR/via-x11" >&2
	exit 1
fi

cd "$MYDIR" || exit $?

# create tmp directory if it does not exist
mkdir -p "$MYDIR/via-x11/tmp" || exit $?
rm -f "$MYDIR/via-x11/tmp"/*

mkdir -p "$MYDIR/via-x11/config" || exit $?

# check if X11 socket is available (should be available in most cases)
if [ "$DISPLAY" != ":0" ]; then
	echo "FATAL: unable to find x11 socket" >&2
	exit 1
fi

# link X11 socket and copy Xauthority file to tmp directory to limit host X11 access
ln -s /tmp/.X11-unix/X0 "$MYDIR/via-x11/tmp/x11-socket" || exit $?
if [ -z "$XAUTHORITY" ]; then
	# shellcheck disable=SC2066
	for XAUTHORITY in "$HOME/.Xauthority" ; do
		if [ -s "$XAUTHORITY" ]; then
			break;
		fi
	done
	if [ ! -s "$XAUTHORITY" ]; then
		echo -e "Failed to find XAUTHORITY file.\nSet XAUTHORITY to the appropriate absolute file path and try again." >&2
		exit 1
	fi
	echo "Found XAUTHORITY file: $XAUTHORITY"
fi
cp "$XAUTHORITY" "$MYDIR/via-x11/tmp/Xauthority" || exit $?

# start the container
docker compose up ipmi-kvm-browser-via-x11 || exit $?

# clean up tmp directory
rm -f "$MYDIR/via-x11/tmp"/*
