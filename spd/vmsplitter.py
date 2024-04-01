from construct import *
import struct
from bmpconverter import BMP, sprd_decompressor, bmap_translate

VM = Struct(
    Const(b"VM"),
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
    "_frames" / Int32ul,
    "frames" / Array(this._frames, Struct(
        "_size" / Int32ul,
        "_offset" / Int32ul,
        "_sizemask" / Computed(this._size & 0x7fffffff),
        "compressed" / Computed((this._size & 0x80000000) == 0),
        "data" / Pointer(this._offset, Bytes(this._sizemask))
    ))
)

VM_BIG = Struct(
    Const(b"MV"),
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
    "_frames" / Int32ub,
    "frames" / Array(this._frames, Struct(
        "_size" / Int32ub,
        "_offset" / Int32ub,
        "_sizemask" / Computed(this._size & 0x7fffffff),
        "compressed" / Computed((this._size & 0x80000000) == 0),
        "data" / Pointer(this._offset, Bytes(this._sizemask))
    ))
)

def load_vm(data):
    vm = VM.parse(data)
    header = vm.copy()
    del header["frames"]    

    framebuf = bytearray(header["dib"]["width"] * header["dib"]["height"] * 3)

    for f in vm["frames"]:        
        out = header.copy()
        assert out["dib"]["bpp"] == 16

        out["dib"]["compression"] &= ~0x1000
        img_offset = 0
        
        if f["compressed"]:
            tempBuf = sprd_decompressor(f["data"], out["dib"]["width"])

        else:
            tempBuf = bmap_translate(f["data"], out["dib"]["width"])

        while img_offset < len(tempBuf):
            if header["reserved_1"] == 0xff and header["reserved_2"] == 0xff:
                if tempBuf[img_offset:img_offset+2] != b"\x1f\xf8":
                    framebuf[img_offset:img_offset+2] = tempBuf[img_offset:img_offset+2]

            elif tempBuf[img_offset:img_offset+2] != header["reserved_1"].to_bytes(2, "little"):
                framebuf[img_offset:img_offset+2] = tempBuf[img_offset:img_offset+2]

            img_offset += 2

        out["data"] = framebuf        
        out["size"] = out["start_offset"] + len(out["data"])

        yield BMP.build(out)

def load_vm_big(data):
    vm = VM_BIG.parse(data)
    header = vm.copy()
    del header["frames"]    

    framebuf = bytearray(header["dib"]["width"] * header["dib"]["height"] * 3)

    for f in vm["frames"]:        
        out = header.copy()
        assert out["dib"]["bpp"] == 16

        out["dib"]["compression"] &= ~0x1000
        img_offset = 0
        
        if f["compressed"]:
            tempBuf = sprd_decompressor(f["data"], out["dib"]["width"], endian=1)

        else:
            tempBuf = bmap_translate(f["data"], out["dib"]["width"], endian=1)

        while img_offset < len(tempBuf):
            if header["reserved_1"] == 0xff and header["reserved_2"] == 0xff:
                if tempBuf[img_offset:img_offset+2] != b"\x1f\xf8":
                    framebuf[img_offset:img_offset+2] = tempBuf[img_offset:img_offset+2]

            elif tempBuf[img_offset:img_offset+2] != header["reserved_1"].to_bytes(2, "little"):
                framebuf[img_offset:img_offset+2] = tempBuf[img_offset:img_offset+2]

            img_offset += 2

        out["data"] = framebuf        
        out["size"] = out["start_offset"] + len(out["data"])

        yield BMP.build(out)
 
if __name__ == "__main__":
    for e, f in enumerate(load_vm(open("test.ani", "rb").read())):
        open(f"test_bmp/img_{e:04d}.bmp", "wb").write(f)
    for e, f in enumerate(load_vm_big(open("test2.ani", "rb").read())):
        open(f"test_bmp2/img_{e:04d}.bmp", "wb").write(f)
        