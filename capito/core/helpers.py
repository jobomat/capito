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


def rgb_int_to_hex(r:int, g:int, b:int, a:int=None, hash:bool=True) -> str:
    """Convert int r,g,b[,a] values to hex color string with or without leading hash."""
    a = f"{a:02x}" if a is not None else ""
    hash = "#" if hash else ""
    return f"{hash}{r:02x}{g:02x}{b:02x}{a}"
    
    
def rgb_int_to_float(r:int, g:int, b:int, a:int=None) -> list[float]:
    """Convert int r,g,b[,a] values to float [r, g, b [,a]] list."""
    rgb = [r / 255, g / 255, b / 255]
    if a:
        rgb.append(a / 255)
    return rgb
    
    
def rgb_float_to_int(r:float, g:float, b:float, a:float=None) -> list[int]:
    """Contvert float rgb[a] values to int [r, g, b[, a]] list."""
    rgb = [int(r * 255), int(g * 255), int(b * 255)]
    if a:
        rgb.append(int(a * 255))
    return rgb


def rgb_float_to_hex(r:float, g:float, b:float, a:float=None, hash:bool=True) -> str:
    """Contvert float rgb[a] values to hex string with or without leading hash."""
    return rgb_int_to_hex(*rgb_float_to_int(r, g, b, a), hash=hash)
    

def hex_to_rgb_int(hex_color: str) -> list[int]:
    """Convert hex rgb string to int [r, g, b [, a]] list."""
    col = hex_color.lstrip("#")
    return [int(col[i : i + 2], 16) for i in range(0, len(col),2)]


def hex_to_rgb_float(hex_color:str) -> list[float]:
    """Convert hex rgb string to float [r, g, b [, a]] list."""
    return rgb_int_to_float(*hex_to_rgb_int(hex_color))


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
