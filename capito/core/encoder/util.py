from pathlib import Path
import re
from typing import Tuple


def guess_sequence_pattern(image: Path) -> Tuple[Path, str, int]:
    """create a filename out of an image sequence file which is suitable as -i parameter for ffmpeg
    Returns a tuple with first element being the ffmpeg suitable path ("path/image.%04d.png"),
    the second element being a glob-suitable pattern ("image.*.png")
    and the third element being the number of the chosen image sequence.
    """
    img = str(image)
    try:
        mo = list(re.finditer('\d+',img))[-1]
        return (
            Path(f"{img[:mo.start()]}%0{len(mo.group())}d{img[mo.end():]}"),
            Path(f"{img[:mo.start()]}*{img[mo.end():]}").name,
            int(mo.group())
        )
    except IndexError:
        return None


#  image = Path(r"E:\maya\projects\tiny_monster_moo\images_0001\tiny_monster_moo_1101.png")
#  seq_tuple = guess_sequence_pattern(image)
#  print(str(seq_tuple[0]))
#  >> E:\maya\projects\tiny_monster_moo\images_0001\tiny_monster_moo_%04d.png
#  print(str(seq_tuple[0]))
#  >> 1101