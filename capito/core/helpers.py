import os
import socket
import struct
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

        host = "substance_painter"
    except:
        pass
    return host


def remap_value(old_min, old_max, new_min, new_max, value):
    """Map value to a new range"""
    old_range = old_max - old_min
    if old_range == 0:
        new_value = new_min
    else:
        new_range = new_max - new_min
        new_value = (((value - old_min) * new_range) / old_range) + new_min
    return new_value


def clamp(n, smallest, largest):
    """clamp n between smallest and largest"""
    return max(smallest, min(n, largest))


def rgb_int_to_hex(rgb: Tuple[int, int, int], include_hash: bool = True):
    """Get a HEX color value from a given RGB color value.
    (255,255,255) -> #ffffff
    """
    return "{}{}{}{}".format(
        "#" if include_hash else "",
        clamp(rgb[0], 0, 255),
        clamp(rgb[1], 0, 255),
        clamp(rgb[2], 0, 255),
    )


def hex_to_rgb_int(hex_color: str) -> Tuple[int, int, int]:
    """Get a RGB int color value from a given HEX color value
    #ffffff -> (255,255,255])
    """
    return tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))


def get_font_dict(font_dir: Path):
    """Given a path to a folder of fonts, return a dict of style:
    {
        FONTNAME: [STYLE1, STYLE2...],
        ...
    }
    The naming convention for the ttf-fonts ist NAME-STYLE.ttf
    """
    font_dict = {}
    for font_file in font_dir.glob("*"):
        font_split = str(font_file.stem).split("-")
        if not font_dict.get(font_split[0]):
            font_dict[font_split[0]] = []
        if len(font_split) > 1:
            font_dict[font_split[0]].append(font_split[1])
    return font_dict


def get_font_file(font_dir: Path, font: str, style: str):
    """Create the absolute path version for a given font (see get_font_dict)"""
    return font_dir / f"{font}-{style}.ttf"


def get_ffmpeg_fontfile(font_dir: Path, font: str, style: str):
    """Create a version of a absolute font-path suitable for ffmpeg-drawtext."""
    fontfile = str(get_font_file(font_dir, font, style))
    fontfile = fontfile.replace("\\", "/")
    if fontfile[0] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
        fontfile = f"{fontfile[0]}\\\\{fontfile[1:]}"
    return fontfile
