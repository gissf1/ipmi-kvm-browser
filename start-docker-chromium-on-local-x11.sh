#!/bin/bash

if [ -z "$DISPLAY" ]; then
	echo "FATAL: DISPLAY environment variable is not set." >&2
	exit 1
fi

MYDIR=$( dirname "$(realpath "$0" )" )

if [ ! -d "$MYDIR/via-x11" ]; then
	echo "FATAL: unable to find via-x11 path in $MYDIR" >&2
	exit 1
fi

cd "$MYDIR" || exit $?

mkdir -p "$MYDIR/via-x11/tmp" || exit $?
rm -f "$MYDIR/via-x11/tmp"/*

mkdir -p "$MYDIR/via-x11/config" || exit $?

if [ "$DISPLAY" != ":0" ]; then
	echo "FATAL: unable to find x11 socket" >&2
	exit 1
fi

ln -s /tmp/.X11-unix/X0 "$MYDIR/via-x11/tmp/x11-socket" || exit $?
cp "$XAUTHORITY" "$MYDIR/via-x11/tmp/Xauthority" || exit $?

docker compose up ipmi-kvm-browser-via-x11 || exit $?

rm -f "$MYDIR/via-x11/tmp"/*
