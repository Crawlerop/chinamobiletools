from construct import *

VIVA = Struct(
    "viva_offset" / FormatField("<", "L"),
    "_zimage" / FormatField("<", "L"),
    "_boot_zimage" / FormatField("<", "L"),
    "_dcmcode" / FormatField("<", "L"),
    "_alice" / FormatField("<", "L"),
    "zimage" / If(this._zimage, Computed(this._zimage - this.viva_offset)),
    "boot_zimage" / If(this._boot_zimage, Computed(this._boot_zimage - this.viva_offset)),
    "dcmcode" / If(this._dcmcode, Computed(this._dcmcode - this.viva_offset)),
    "alice" / If(this._alice, Computed(this._alice - this.viva_offset))
)

zPartition = Struct(
    "_partition_count" / FormatField("<", "L"),
    "partitions" / Array(this._partition_count, Struct(
        "compression_type" / FormatField("<", "L"),
        "src_address" / FormatField("<", "L"),
        "src_size" / FormatField("<", "L"),
        "dst_address" / FormatField("<", "L"),
        "dst_size" / FormatField("<", "L"),
        "data" / Pointer(this.src_address, Bytes(this.src_size))
    ))    
)