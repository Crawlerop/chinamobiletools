from construct import *
import bmpconverter
import sprd_abm
import argparse
import os

SRES = Struct(
    "magic" / Const(b"sres0001"),
    "unk1" / Hex(Int32ul),
    "unk2" / Hex(Int8ul),
    "count_after_tres" / Hex(Int8ul),
    "unk3" / Hex(Int16ul),
    "tres" / Array(33, Struct(
        "_offset" / Hex(Int32ul),
        "_size" / Hex(Int32ul),
        "tres" / Pointer(this._offset, Bytes(this._size)),
    )),
    "unk4" / Hex(Int32ul),
    "post_tres" / Array(this.count_after_tres, Struct(
        "id" / PaddedString(4, "utf-8"),
        "_offset" / Hex(Int32ul),
        "_size" / Hex(Int32ul),
        "data" / Pointer(this._offset, Bytes(this._size))
    ))
)   

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("in_sres")
    ap.add_argument("out_folder")
    args = ap.parse_args()
    
    os.makedirs(os.path.join(args.out_folder, "TRES/"), exist_ok=True)
    
    sres = SRES.parse_file(args.in_sres)
    for i, tres in enumerate(sres.tres):
        if len(tres.tres) <= 0: continue
        open(os.path.join(args.out_folder, "TRES/", f"{i+1}.bin"), "wb").write(tres.tres)
        
    for part in sres.post_tres:
        if part.id == "logo":
            if part.data[:3] == b"ABM":
                i, m = sprd_abm.decompress(part.data)
                if len(m) <= 0:
                    i.save(os.path.join(args.out_folder, f"{part.id}.abm.png"))
                    
                else:
                    i.save(os.path.join(args.out_folder, f"{part.id}.abm.png"), transparency=bytes(m))
                    
                    
            else:
                open(os.path.join(args.out_folder, f"{part.id}.bmp"), "wb").write(bmpconverter.translate_bmp(part.data))
                
        else:
            open(os.path.join(args.out_folder, f"{part.id}.bin"), "wb").write(part.data)