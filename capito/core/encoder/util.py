"""Module providing helper classes and functions for encoder"""
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Tuple

from capito.core.helpers import get_ffmpeg_fontfile


def guess_sequence_pattern(image: Path) -> Tuple[Path, str, int]:
    """create a filename out of an image sequence file which is suitable as -i parameter for ffmpeg
    Returns a tuple with first element being the ffmpeg suitable path ("path/image.%04d.png"),
    the second element being a glob-suitable pattern ("image.*.png")
    and the third element being the number of the chosen image sequence.
    """
    img = str(image)
    try:
        mo = list(re.finditer("\d+", img))[-1]
        return (
            Path(f"{img[:mo.start()]}%0{len(mo.group())}d{img[mo.end():]}"),
            Path(f"{img[:mo.start()]}*{img[mo.end():]}").name,
            int(mo.group()),
        )
    except IndexError:
        return None


def transform_framenumber(drawtext, padding=4, start=None):
    """Create a suitable framnumber counter string for ffmpeg"""
    startframe = start or drawtext.encoder.startframe
    return f"%{{eif\:n+{startframe}\:d\:{padding}}}"


def transform_datetime(drawtext, format="%d.%m.%Y - %H\:%M"):
    """Return the current date and time formated according to 'format'."""
    time = datetime.now()
    return time.strftime(format)


def transform_outfilename(drawtext, full_path=False):
    """Returns the specified output filename (*.mp4)"""
    filepath = Path(drawtext.encoder.output_file)
    if not full_path:
        filepath = filepath.name
    return str(filepath).replace("\\", "/").replace(":", r"\:")


def transform_projectname(*args):
    """Return the capito projectname."""
    capito_project_dir = os.environ.get("CAPITO_PROJECT_DIR")
    if capito_project_dir is None:
        return "UNKNOWN PROJECT"
    project_path = Path(capito_project_dir)
    project_conf = project_path / "capito_conf.json"
    if not project_conf.exists():
        return project_path.stem
    with project_conf.open("r") as conf_fp:
        config = json.load(conf_fp)
        return config.get("project_name", project_path.stem)


def overrides(*args, **kwargs):
    """
    Method to pass through the burnin overrides without needeng an extra mechanism.
    (fontsize, fontcolor, fontfile, offset_x, offset_y, boxcolor, boxborderw)
    """
    return kwargs


@dataclass
class DrawText:
    """Class for generating correct ffmpeg 'drawtext' flags."""

    pos: str
    text: str
    encoder: Any

    def __post_init__(self):
        self.margins = self.encoder.burnin_defaults["margins"]
        self.font_color = self.encoder.burnin_defaults["font_color"]
        self.font_opacity = self.encoder.burnin_defaults["font_opacity"]
        self.font_tuple = self.encoder.burnin_defaults["font_tuple"]
        self.font_size = self.encoder.burnin_defaults["font_size"]
        self.box_color = self.encoder.burnin_defaults["box_color"]
        self.box_opacity = self.encoder.burnin_defaults["box_opacity"]
        self.box_padding = self.encoder.burnin_defaults["box_padding"]

        self.lines = [l for l in self.text.split("\n") if l]
        font_folder = Path(os.environ.get("CAPITO_BASE_DIR"), "resources", "fonts")
        self.font_file = get_ffmpeg_fontfile(font_folder, *self.font_tuple)
        self.regex = re.compile(r"(?<!\\)(<.*?(?<!\\)>)")
        self.transformers = {
            "frame": transform_framenumber,
            "datetime": transform_datetime,
            "outfile": transform_outfilename,
            "projectname": transform_projectname,
            "overrides": overrides,
        }
        self.y_pos, self.x_pos = self.pos.split("_")
        if self.y_pos == "bottom":
            self.lines.reverse()

    def get_font_color(self):
        """Get ffmpeg-style color-representation for the font."""
        return f"{self.font_color}@{float(self.font_opacity) / 100.0}"

    def get_box_color(self):
        """Get ffmpeg-style color-representation for the box."""
        return f"{self.box_color}@{float(self.box_opacity) / 100.0}"

    def transform_text(self, value):
        """Returns a tuple of function_key and either the
        the transformed value according to the registered function found by function_key
        or if no function was found in function_key the original value"""
        tag_value = value[1:-1]
        transformer, *args = tag_value.split(":")
        kwargs = {}
        for arg in args:
            k, v = arg.split("=")
            kwargs[k] = v
        func_key = transformer.lower()
        func = self.transformers.get(func_key, None)
        return (func_key, value) if func is None else (func_key, func(self, **kwargs))

    def get_drawtext(self):
        """Returns the drawtext."""
        drawtexts = []
        y = self.margins[self.y_pos]
        for line in self.lines:
            parts = []
            matches = {}
            replace_dict = {}
            for match in self.regex.findall(line):
                key, val = self.transform_text(match)
                matches[key] = val
                replace_dict[match] = val
            overrides = matches.get("overrides", {})
            parts.extend(self.get_font_and_box_properties(overrides))
            y = self.sum_y_position(overrides, y)
            y_string = y if self.y_pos == "top" else f"h-{y}"
            parts.append(f"y={y_string}")
            parts.append(self.get_x_position(overrides))
            parts.append(self.get_text(replace_dict, line))
            drawtexts.append(":".join(parts))
        return ",drawtext=".join(drawtexts)

    def sum_y_position(self, overrides, current_y):
        """Calculating the y shift of a box/textline by taking into account
        the screen-margin, the fontsize, the boxpadding and the overrides
        TODO: Check the results if overrides are used... not quite right..."""
        if current_y == self.margins[self.y_pos] and self.y_pos == "top":
            font_size = 0
        else:
            font_size = int(overrides.get("fontsize", self.font_size))
        border_padding = int(overrides.get("boxborderw", self.box_padding))
        offset = int(overrides.get("offset_y", 0))
        return current_y + font_size + border_padding + offset

    def get_x_position(self, overrides):
        """Calculating the x shift of a box/textline by taking into account
        the screen-margin and the overrides"""
        offset = int(overrides.get("offset_x", 0))
        margin = self.margins[self.y_pos]
        if self.x_pos == "left":
            return f"x={margin + offset}"
        elif self.x_pos == "center":
            return f"x=(w-text_w)/2+{offset}"
        else:
            return f"x=w-tw-{margin + offset}"

    def get_text(self, replace_dict, line):
        """Getting the text by searching for the detected placeholders
        and replacing them with their transformed versions.
        eg. <FRAME> --> 1001"""
        for search, replace in replace_dict.items():
            if not isinstance(replace, str):
                replace = ""
            line = line.replace(search, replace)
        return f"text='{line}'" if line else ""

    def get_font_and_box_properties(self, overrides):
        """Get either the override values or the defaults"""
        return [
            f"fontsize={overrides.get('fontsize', self.font_size)}",
            f"fontcolor={overrides.get('fontcolor', self.get_font_color())}",
            f"fontfile={overrides.get('fontfile', self.font_file)}",
            "box=1",
            f"boxcolor={overrides.get('boxcolor', self.get_box_color())}",
            f"boxborderw={overrides.get('boxborderw', self.box_padding)}",
        ]
