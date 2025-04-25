import sprd_abm
from construct import *

SMOV = Struct(
    Const(b"SMOV"),
    Const(b"ARGB"),
    "bpp" / Int16ub,
    "_frames" / Int16ub,
    Int32ub,
    "frame_offsets" / Array(this._frames, Int32ub)
)

def smov_get(data):
    smov = SMOV.parse(data)
    
    for fo in smov.frame_offsets:
        yield sprd_abm.decompress(data[fo:])