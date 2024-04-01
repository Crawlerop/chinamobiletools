from construct import *

BootLoader = Struct(
    Const(b"SF_BOOT\x00\x00\x00\x00\x00"),
    "version" / FormatField("<", "L"),
    "dev_rw_unit" / FormatField("<", "L"),
    "layout" / Pointer(this.dev_rw_unit, Struct(
        Const(b"BRLYT\0\0\0"),
        "version" / FormatField("<", "L"),
        "bootloader_start" / FormatField("<", "L"),
        "bootloader_end" / FormatField("<", "L"),
        "regions" / Array(8, Struct(
            "bl_exist" / Bytes(4),
            "flash_dev" / FormatField("<", "H"),
            "flash_type" / FormatField("<", "H"),
            "start" / FormatField("<", "L"),
            "end" / FormatField("<", "L")
        ))
    ))
)