# ipmi-kvm-browser

## About

This project provides a containerized solution for accessing older IPMI KVM interfaces and Java Applet-based utilities from modern systems. It eliminates the need to install outdated Java runtimes on your host system, confining them to a container for improved security.

Key features:
- Containerized environment for legacy Java Applet-based utilities, such as IPMI KVM interfaces
- Two modes of operation: VNC and pure X11
- Simplified software stack

This work is based on:
- https://github.com/solarkennedy/ipmi-kvm-docker
- https://github.com/sciapp/nojava-ipmi-kvm

## Background

This tool addresses the need to access older Java Applet-based interfaces, such as IPMI KVMs.  By containerizing outdated Java runtimes and browser stacks, it minimizes exposure of the host system to potential vulnerabilities while maintaining functionality.  It also aims to reduce the complexity of the employed software stack.  X11 and VNC have long provided smooth experiences for many remote GUI applications.  While previous projects have tried integrating noVNC, this project avoids that unnecessary complication to maintain full functionality.


## Modes of Operation

There are 2 modes of operation:

| Method | Description | Security | Performance | Pros | Cons |
|--------|-------------|----------|-------------|------|------|
| VNC    | Accesses Java and older Chromium through a VNC viewer. | More Secure | Higher resource usage | Prevents direct access to the host system. | Screen resolution is fixed at runtime |
| X11    | Containerized Chromium communicates with the host X11 server. | Less Secure | Lower resource usage | Browser stack and Java Applets appear as native application windows on the local X11 desktop, allowing seamless integration with host desktop. | Exposes host X11 session to potential vulnerabilities |

**Note**: X11 mode is recommended only for advanced users who are cautious about accessed content.

### VNC Mode
In VNC mode, Java and the older Chromium are accessed through a VNC viewer, preventing direct access to your host system. Note that the default VNC screen size may not match your host or may conflict with desired window sizes.

### X11 Mode
X11 mode passes the local X11 socket and .Xauthority authentication key into the container. This allows the containerized Chromium and Java to directly communicate with your native host X11 server, appearing on your native X11 desktop as local applications.

While this mode restricts most direct file access to your host system, it exposes your host's X11 session to potential risks from older software. It offers lower resource utilization and better integration with the host desktop, but is only recommended for advanced users who understand and can mitigate the associated risks.

## Usage
To launch in VNC mode:
```bash
docker compose up ipmi-kvm-browser
# Now direct your favorite VNC viewer to connect to localhost:1 to access the container's X11 desktop session.
```

To launch in X11 mode:
```bash
./start-docker-chromium-on-local-x11.sh
# Now Chromium will launch in its own window.
```
you may want to make sure to disable "run in background" and similar options that are inappropriate in this context.

## Requirements
- Docker
- Docker Compose
- X11 server (for X11 mode)
- VNC viewer (for VNC mode)

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

