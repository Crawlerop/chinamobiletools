from construct import *
from PIL import Image
import struct
import sprd_abm
import sjpgtojpg
import vmsplitter
import smovsplitter
import bmpconverter
import argparse
import os

# 01 - Icons
# 02 - Animation
# 03 - Ringtone
# 04 - Strings
# 05 - Font
# 06 - WAP Presets
# 07 - Unknown
# 08 - Unknown

_TRES_ICON = Struct(
    "_info_base" / Hex(Int32ul),
    "_offsets_base" / Hex(Int32ul),
    "_offsets" / Pointer(this._offsets_base + this._._._data_base_ptr, Array(this._._count, Struct(
        "offset" / Hex(Int32ul)
    ))),
    "info" / Pointer(this._info_base + this._._._data_base_ptr, Array(this._._count, Struct(
        "_index" / Index,
        "width" / Int16ul,
        "height" / Int16ul,
        "type" / Hex(Int32ul),
        "_size" / Hex(Int32ul),
        "_computed_offs" / Computed(lambda x: x._._offsets[x._index].offset + x._._._._data_base_ptr),
        "data" / Pointer(this._computed_offs, Bytes(this._size))
    )))
)

_TRES_ANIM = Struct(
    "_info_base" / Hex(Int32ul),
    "_offsets_base" / Hex(Int32ul),
    "_offsets" / Pointer(this._offsets_base + this._._._data_base_ptr, Array(this._._count, Struct(
        "offset" / Hex(Int32ul)
    ))),
    "info" / Pointer(this._info_base + this._._._data_base_ptr, Array(this._._count, Struct(
        "_index" / Index,
        "width" / Int16ul,
        "height" / Int16ul,
        "type" / Hex(Int16ul),
        "frames" / Int16ul,
        "_size" / Hex(Int32ul),
        "_computed_offs" / Computed(lambda x: x._._offsets[x._index].offset + x._._._._data_base_ptr),
        "data" / Pointer(this._computed_offs, Bytes(this._size))
    )))
)

_TRES_AUDIO = Array(this._count, Struct(    
    "type" / Hex(Int32ul),
    "_size" / Hex(Int32ul),
    "_offset" / Hex(Int32ul),
    "data" / Pointer(this._offset + this._._._data_base_ptr, Bytes(this._size))
))

_TRES_DATA = Struct(
    "_data_base_ptr" / Tell,
    "data" / Array(8, Struct(
        "index" / Index,
        "_offset" / Hex(Int32ul),
        "_count" / Int32ul,
        "_size" / Hex(Int32ul),
        StopIf(this._count <= 0),
        "table" / Pointer(this._offset + this._._data_base_ptr, Switch(this.index, {0: _TRES_ICON, 1: _TRES_ANIM, 2: _TRES_AUDIO}, Struct("data" / Bytes(this._._size))))
    ))
)

TRES = Struct(
    "magic" / Const(b"tres0001"),
    "unk1" / Hex(Int32ul),
    "unk2" / Hex(Int32ul),
    "end" / Hex(Int32ul),
    "list" / Array(0x40, Struct(
        "_index" / Hex(Int32ul),
        StopIf(this._index <= 0),
        StopIf(this._index >= this._.end),
        "data_ptr" / Pointer(this._index, _TRES_DATA)
    ))
)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("in_tres")
    ap.add_argument("out_folder")
    args = ap.parse_args()
    
    s = TRES.parse_file(args.in_tres)
    os.makedirs(os.path.join(args.out_folder, "Icon/"), exist_ok=True)
    os.makedirs(os.path.join(args.out_folder, "Animation/"), exist_ok=True)
    os.makedirs(os.path.join(args.out_folder, "Sound/"), exist_ok=True)
    os.makedirs(os.path.join(args.out_folder, "String/"), exist_ok=True)
    
    img_id = 1
    anim_id = 1
    sound_id = 1
    string_id = 1
    
    for k in s.list:
        if "data_ptr" not in k: continue
        
        if "table" in k.data_ptr.data[0]:
            for icon in k.data_ptr.data[0].table.info:
                if len(icon.data) <= 0: continue
                if icon.type in [0x316, 0x30c]: # ABM
                    img, mask = sprd_abm.decompress(icon.data)
                    if len(mask) <= 0:
                        img.save(os.path.join(args.out_folder, "Icon/", f"{img_id}.abm.png"))
                        
                    else:
                        img.save(os.path.join(args.out_folder, "Icon/", f"{img_id}.abm.png"), transparency=bytes(mask))
                    
                elif icon.type in [0x31a, 0x310]: # SABM
                    assert icon.data[:4] == b"sabm"
                    if icon.data[6]:
                        img, mask = sprd_abm.decompress(icon.data[0xc:])
                        if len(mask) <= 0:
                            img.save(os.path.join(args.out_folder, "Icon/", f"{img_id}.sabm_abm.png"))
                            
                        else:
                            img.save(os.path.join(args.out_folder, "Icon/", f"{img_id}.sabm_abm.png"), transparency=bytes(mask))
                            
                    else:
                        width, height = struct.unpack(">HH", icon.data[0x8:0xc])
                        Image.frombytes("RGBA", (width, height), icon.data[0xc:]).save(os.path.join(args.out_folder, "Icon/", f"{img_id}.sabm.png"))
                    
                elif icon.type == 0x108: # SGIF
                    assert icon.data[:4] == b"SGIF"
                    open(os.path.join(args.out_folder, "Icon/", f"{img_id}.gif"), "wb").write(icon.data[0xc:])
                    
                elif icon.type == 0x20a: # SJPG
                    open(os.path.join(args.out_folder, "Icon/", f"{img_id}.jpg"), "wb").write(sjpgtojpg.sjpg_to_jpg(icon.data))
                    
                elif icon.type == 0x420:
                    open(os.path.join(args.out_folder, "Icon/", f"{img_id}.bin"), "wb").write(icon.data)
                    
                else: # BMP
                    open(os.path.join(args.out_folder, "Icon/", f"{img_id}.bmp"), "wb").write(bmpconverter.translate_bmp(icon.data))
                    
                img_id += 1
        
        if "table" in k.data_ptr.data[1]:
            for anim in k.data_ptr.data[1].table.info:
                if anim.type == 0x303:
                    for i, (img, mask) in enumerate(smovsplitter.smov_get(anim.data)):
                        if len(mask) <= 0:
                            img.save(os.path.join(args.out_folder, "Animation/", f"{anim_id}.smov_{i+1:04d}.png"))
                            
                        else:
                            img.save(os.path.join(args.out_folder, "Animation/", f"{anim_id}.smov_{i+1:04d}.png"), transparency=bytes(mask))
                    
                else:
                    for i, f in enumerate(vmsplitter.load_vm(anim.data)):
                        open(os.path.join(args.out_folder, "Animation/", f"{anim_id}.vm_{i+1:04d}.bmp"), "wb").write(f)
                        
                anim_id += 1
        
        if "table" in k.data_ptr.data[2]:
            for ringtone in k.data_ptr.data[2].table:
                if len(ringtone.data) <= 0: continue
                if ringtone.type == 0:
                    open(os.path.join(args.out_folder, "Sound/", f"{sound_id}.mid"), "wb").write(ringtone.data)
                    
                elif ringtone.type == 5:
                    open(os.path.join(args.out_folder, "Sound/", f"{sound_id}.wav"), "wb").write(ringtone.data)
                    
                elif ringtone.type == 6:
                    open(os.path.join(args.out_folder, "Sound/", f"{sound_id}.mp3"), "wb").write(ringtone.data)
                    
                elif ringtone.type == 8:
                    open(os.path.join(args.out_folder, "Sound/", f"{sound_id}.amr"), "wb").write(ringtone.data)
                    
                sound_id += 1
                
        if "table" in k.data_ptr.data[3]:
            open(os.path.join(args.out_folder, "String/", f"{string_id}.bin"), "wb").write(k.data_ptr.data[3].table.data)
            string_id += 1