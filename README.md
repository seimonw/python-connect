# python-wifi-connect (forked from)
An application that displays an IP address configuration UI for BalenaOS devices.

Inspired by the [wifi-connect](https://github.com/balena-io/wifi-connect) project written by [balena.io](https://www.balena.io/). Modified from the Python version created by [Open Agriculture Foundation](https://github.com/OpenAgricultureFoundation/python-wifi-connect)

# Install and Run

Please read the [INSTALL.md](INSTALL.md) then the [RUN.md](RUN.md) files.


# How it works
WiFi Connect interacts with NetworkManager, which should be the active network manager on the device's host OS.


## References
- This application uses the [python-networkmanager module](https://pypi.org/project/python-networkmanager/). 
- Source for the [python-networkmanager module](https://github.com/seveas/python-networkmanager) on GitHub.
- Documentation for the [python-networkmanager module](https://pythonhosted.org/python-networkmanager/).
- The above python module is just an API that communicates over DBUS to the [debian NetworkManager package](https://wiki.debian.org/NetworkManager) which must be installed.
- [DBUS NetworkManager API](https://developer.gnome.org/NetworkManager/1.2/spec.html)
- [The Rust language version of this application written by balena.io](https://github.com/balena-io/wifi-connect) is a great reference!
- [The original Python version from Open Agriculture Foundation](https://github.com/OpenAgricultureFoundation/python-wifi-connect)

