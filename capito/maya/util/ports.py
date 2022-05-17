import pymel.core as pc


def open_port(port):
    port_str = ":{}".format(port)
    if port_str in pc.commandPort(q=True, listPorts=True):
        print("Port {} already open.".format(port))
        return True

    pc.commandPort(name=port_str, sourceType="python")
    print("Port {} opened.".format(port))


def close_port(port):
    port_str = ":{}".format(port)
    if port_str not in pc.commandPort(q=True, listPorts=True):
        print("No port {} found.".format(port))
        return
    pc.commandPort(name=port_str, close=True)
    print("Port {} closed.".format(port))


def toggle_port(port):
    port_str = ":{}".format(port)
    if port_str in pc.commandPort(q=True, listPorts=True):
        close_port(port)
    else:
        open_port(port)


def toggle_sublime_port():
    toggle_port(7002)
