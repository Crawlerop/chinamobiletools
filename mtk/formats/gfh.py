from construct import *

_GFH_FIND_REGEX = bytes.fromhex("4D 4D 4D 01 38 00 00 00 46 49 4C 45 5F 49 4E 46 4F 00 00 00")

GFH = Struct(
    Const(b"MMM"),
    "gfh_version" / FormatField("<", "B"),
    "size" / FormatField("<", "H"),
    "type" / FormatField("<", "H"),
    "data" / Bytes(this.size-8)    
)

FileInfo = Struct(
    Const(b"FILE_INFO\0\0\0"),
    "info_version" / FormatField("<", "L"),
    "info_type" / FormatField("<", "H"),
    "info_dev" / FormatField("<", "B"),
    "info_sig_type" / FormatField("<", "B"),
    "info_load_addr" / FormatField("<", "L"),
    "info_file_len" / FormatField("<", "L"),
    "info_max_size" / FormatField("<", "L"),
    "info_content_offset" / FormatField("<", "L"),
    "info_sig_len" / FormatField("<", "L"),
    "info_jump_offset" / FormatField("<", "L"),
    "info_attr" / FormatField("<", "L"),
)

BootLoaderInfo = Struct(
    "attr" / FormatField("<", "L")   
)

ArmBootLoaderInfo = Struct(
    "maui_paired_version" / FormatField("<", "L"),
    "feature_combination" / FormatField("<", "L"),
    "feature_combination_ex" / FormatField("<", "L"),
    "fdm_dal_version" / Bytes(8),
)

def findGFH(data):
    data = bytearray(data)
    offset = data.find(_GFH_FIND_REGEX)

    gfhs = []

    while offset != -1:
        gfh = GFH.parse(data[offset:])
        file_info = FileInfo.parse(gfh.data)        
        gfhs.append((file_info, data[offset:offset+(file_info.info_file_len+file_info.info_sig_len)]))
        offset = data.find(_GFH_FIND_REGEX, offset+1)

    return gfhs
#MauiInfo1 = Struct()