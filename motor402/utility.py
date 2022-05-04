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
