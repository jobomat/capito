hexToIntMap = {str(x): x for x in range(10)}
hexToIntMap.update(
    {"a": 10, "b": 11, "c": 12, "d": 13, "e": 14, "f": 15}
)
intToHexMap = {v: k for k, v in hexToIntMap.items()}


def isListOfInts(il):
    if not isinstance(il, list):
        print ("Please specify value as List of ints (eg. [120, 54, 0])")
        return False
    if not all([isinstance(i, int) for i in il]):
        print ("Every list-item has to be of type int.")
        return False
    return True


def isListOfFloats(fl):
    if not isinstance(fl, list):
        print ("Please specify value as List of Floats (eg. [0.2, 0.5, 1])")
        return False
    if not all([isinstance(f, float) for f in fl]):
        print ("Every list-item has to be of type float.")
        return False
    return True


def hexToInt(h):
    h = h.lower()
    allowedChars = "0123456789abcdef#"
    if not all(c in allowedChars for c in h):
        print ("Hex color values may only contain characters 0-9 and a-f.")
        return []
    if not isinstance(h, str):
        print ("Please specify value as String ('ffo3c2' or '#ffo3c2')")
        return []
    if h[0] == "#":
        h = h[1:]
    if len(h) % 2:
        print ("Color hex value has to be multiple of 2. ('ff' or '#ff')")
        return []
    ret = []
    for i in range(0, len(h), 2):
        ret.append(hexToIntMap[h[i]] * 16 + hexToIntMap[h[i+1]])
    return ret


def floatToInt(fl):
    if isListOfFloats(fl):
        return [int(f * 255) for f in fl]
    return []

def intToFloat(il):
    if isListOfInts(il):
        return [float(i) / 255 for i in il]
    return []
  

def hexToFloat(h):
    return intToFloat(hexToInt(h))


def intToHex(il):
    if isListOfInts(il):
        h = ""
        for i in il:
            div, mod = divmod(i, 16)
            h += "{}{}".format(intToHexMap[div], intToHexMap[mod])
        return h
    return ""

def floatToHex(fl):
    if isListOfFloats(fl):
        il = [int(f * 255) for f in fl]
        return intToHex(il)
    return ""
