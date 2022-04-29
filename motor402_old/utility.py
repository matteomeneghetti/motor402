import struct

def uint8(value):
    return struct.pack("<B", value)

def int8(value):
    return struct.pack("<b", value)

def uint16(value):
    return struct.pack("<H", value)

def int16(value):
    return struct.pack("<h", value)

def uint32(value):
    return struct.pack("<I", value)

def int32(value):
    return struct.pack("<i", value)

def read_u(value):
    if len(value) == 1:
        return struct.unpack("<B", value)[0]
    elif len(value) == 2:
        return struct.unpack("<H", value)[0]
    elif len(value) == 4:
        return struct.unpack("<I", value)[0]

def read_i(value):
    if len(value) == 1:
        return struct.unpack("<b", value)[0]
    elif len(value) == 2:
        return struct.unpack("<h", value)[0]
    elif len(value) == 4:
        return struct.unpack("<i", value)[0]
