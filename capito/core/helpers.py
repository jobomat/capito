import socket
import struct
import os
from pathlib import Path
from typing import Tuple

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


def detect_host():
    host = "system"
    try:
        import maya
        host = "maya"
    except ImportError:
        pass
    try:
        import nuke
        host = "nuke"
    except ImportError:
        pass
    try:
        import substance_painter
        host ="substance_painter"
    except:
        pass
    return host


def remap_value(old_min, old_max, new_min, new_max, value):
    old_range = (old_max - old_min)
    if old_range == 0:
        new_value = new_min
    else:
        new_range = (new_max - new_min)  
        new_value = (((value - old_min) * new_range) / old_range) + new_min
    return new_value


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))


def rgb_int_to_hex(rgb:Tuple[int, int, int], include_hash:bool=True):
    return "{}{}{}{}".format(
        "#" if include_hash else "",
        clamp(rgb[0], 0, 255),
        clamp(rgb[1], 0, 255),
        clamp(rgb[2], 0, 255)
    )


def get_font_dict(font_dir:Path=None):
    if not font_dir:
        return
        
    font_dict = {}    
    for font_file in font_dir.glob("*"):
        font_split = str(font_file.stem).split("-")
        if not font_dict.get(font_split[0]):
            font_dict[font_split[0]] = []
        if len(font_split) > 1:
            font_dict[font_split[0]].append(font_split[1])

    return font_dict