import socket
import struct

REF_TIME_1970 = 2208988800  # Reference time


def time_from_ntp(addr="0.de.pool.ntp.org"):
    """Get time from an ntp time server."""
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = b"\x1b" + 47 * b"\0"
    client.sendto(data, (addr, 123))
    data, _ = client.recvfrom(1024)
    if data:
        zeit = struct.unpack("!12I", data)[10]
        zeit -= REF_TIME_1970
    return zeit


print(time_from_ntp())
