import struct

def uint8(value):
    return struct.pack("<B", int(value))

def int8(value):
    return struct.pack("<b", int(value))

def uint16(value):
    return struct.pack("<H", int(value))

def int16(value):
    return struct.pack("<h", int(value))

def uint32(value):
    return struct.pack("<I", int(value))

def int32(value):
    return struct.pack("<i", int(value))
