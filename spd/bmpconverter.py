from construct import *
import struct

BMP = Struct(
    Const(b"BM"),
    "size" / Hex(Int32ul),
    "reserved_1" / Int16ul,
    "reserved_2" / Int16ul,
    "start_offset" / Hex(Int32ul),
    "dib" / Struct(
        Const(0x28, Int32ul),
        "width" / Int32ul,
        "height" / Int32ul,
        Const(1, Int16ul),
        "bpp" / Int16ul,
        "compression" / Hex(Int32ul),
        "img_size" / Hex(Int32ul),
        "hres" / Int32ul,
        "vres" / Int32ul,
        "no_colors" / Int32ul,
        "important_colors" / Int32ul,
        "bit_mask" / If((this.compression & 0xff) == 0x3, Array(3, Hex(Int32ul))),
        "palette" / If(this.bpp <= 8, Struct(
            "_palette_size" / Computed(2 ** 4 if this.no_colors <= 0 else this.no_colors),
            "palette" / Bytes(this._palette_size * 4)
        ))                
    ),    
    "_cur" / Tell,
    Check(this._cur == this.start_offset),
    "data" / Bytes(this.size - this.start_offset)
)

BMP_BIG = Struct(
    Const(b"MB"),
    "size" / Hex(Int32ub),
    "reserved_1" / Int16ub,
    "reserved_2" / Int16ub,
    "start_offset" / Hex(Int32ub),
    "dib" / Struct(
        Const(0x28, Int32ub),
        "width" / Int32ub,
        "height" / Int32ub,
        Const(1, Int16ub),
        "bpp" / Int16ub,
        "compression" / Hex(Int32ub),
        "img_size" / Hex(Int32ub),
        "hres" / Int32ub,
        "vres" / Int32ub,
        "no_colors" / Int32ub,
        "important_colors" / Int32ub,
        "bit_mask" / If((this.compression & 0xff) == 0x3, Array(3, Hex(Int32ub))),
        "palette" / If(this.bpp <= 8, Struct(
            "_palette_size" / Computed(2 ** 4 if this.no_colors <= 0 else this.no_colors),
            "palette" / Bytes(this._palette_size * 4)
        ))                
    ),    
    "_cur" / Tell,
    Check(this._cur == this.start_offset),
    "data" / Bytes(this.size - this.start_offset)
)

def bmap_translate(data, width_align: int=0, endian=0):
    offset = 0
    out_temp = bytearray()

    need_align = bool(width_align & 1)
    oWidth = width_align

    while offset < len(data):
        out_temp += data[offset:offset+2] if endian == 0 else (data[offset+1:offset+2] + data[offset:offset+1])
        offset += 2

        '''
        if need_align:
            oWidth -= 1
            if oWidth <= 0:
                oWidth = width_align
                out_temp += b"\0\0"
        '''

    return out_temp

def sprd_decompressor(data, width_align: int=0, endian=0):
    offset = 0
    out_temp = bytearray()

    need_align = bool(width_align & 1)
    oWidth = width_align

    while offset < len(data):
        if endian == 0:
            pixels, count = struct.unpack("<BB", data[offset:offset+2])

        else:
            count, pixels = struct.unpack("<BB", data[offset:offset+2])

        offset += 2
        
        if pixels <= 0 and count <= 0: continue
        
        for _ in range(pixels):
            out_temp += data[offset:offset+2] if endian == 0 else (data[offset+1:offset+2] + data[offset:offset+1])
            offset += 2

            if need_align:
                oWidth -= 1
                if oWidth <= 0:
                    oWidth = width_align
                    out_temp += b"\0\0"

        if count > 0:
            t = data[offset:offset+2] if endian == 0 else (data[offset+1:offset+2] + data[offset:offset+1])
            offset += 2

            for _ in range(count):
                out_temp += t

                if need_align:
                    oWidth -= 1
                    if oWidth <= 0:
                        oWidth = width_align
                        out_temp += b"\0\0"

    return out_temp

def translate_bmp(data):
    s = BMP.parse(data)
    if s["dib"]["compression"] & 0xff00 == 0x1000 and s["dib"]["bpp"] == 16:
        s["dib"]["compression"] &= ~0x1000
        s["data"] = sprd_decompressor(s["data"], s["dib"]["width"])        
        s["size"] = s["start_offset"] + len(s["data"])

    elif s["dib"]["compression"] & 0xff00 == 0x0000 and s["dib"]["bpp"] == 16:
        s["data"] = bmap_translate(s["data"], s["dib"]["width"])
        s["size"] = s["start_offset"] + len(s["data"])

    return BMP.build(s)

def translate_bmp_big(data):
    s = BMP_BIG.parse(data)
    if s["dib"]["compression"] & 0xff00 == 0x1000 and s["dib"]["bpp"] == 16:
        s["dib"]["compression"] &= ~0x1000
        s["data"] = sprd_decompressor(s["data"], s["dib"]["width"], endian=1)        
        s["size"] = s["start_offset"] + len(s["data"])

    elif s["dib"]["compression"] & 0xff00 == 0x0000 and s["dib"]["bpp"] == 16:
        s["data"] = bmap_translate(s["data"], s["dib"]["width"], endian=1)
        s["size"] = s["start_offset"] + len(s["data"])

    return BMP.build(s)

if __name__ == "__main__":
    open("test_sm.bmp", "wb").write(translate_bmp(open("smobile.bmp", "rb").read()))
    open("mx.bmp", "wb").write(translate_bmp_big(open("mb.bmp", "rb").read()))
    