import ctypes
import struct
import os

_mtkLZMA = None
try:
    _mtkLZMA = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "libmtklzma.so"))
except Exception:
    try:
        _mtkLZMA = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "./MTKLZMA.64.dll"))
    except Exception:
        _mtkLZMA = ctypes.CDLL(os.path.join(os.path.dirname(__file__), "./MTKLZMA.32.dll"))

_decompTrain = _mtkLZMA.lzma_uncompress_train
_decompTrain.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
_decompTrain.restype = ctypes.c_int

_decomp = _mtkLZMA.lzma_uncompress
_decomp.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]
_decomp.restype = ctypes.c_int

_transform = _mtkLZMA.transformProcess
_transform.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]

def decompress(data, train=None):
    if train is None:
       pIn = (ctypes.c_ubyte * len(data)).from_buffer(bytearray(data))
       pOutSize = struct.unpack("<Q", data[5:13])[0]
       pOut = (ctypes.c_ubyte * pOutSize)()

       res = _decomp(pOut, pOutSize, pIn, len(data))
       assert res == 0, f"LZMADecode returned -{res}"

       return bytes(pOut)

    else:
       pIn = (ctypes.c_ubyte * len(data)).from_buffer(bytearray(data))
       pOutSize = struct.unpack("<Q", data[5:13])[0]
       pTrain = (ctypes.c_ubyte * len(train)).from_buffer(bytearray(train))
       pOut = (ctypes.c_ubyte * pOutSize)()

       res = _decompTrain(pOut, pOutSize, pIn, len(data), pTrain, len(train))
       assert res == 0, f"LZMADecode returned -{res}"

       return bytes(pOut)
    
def transformProcess(data):
    pIn = (ctypes.c_ubyte * len(data)).from_buffer(bytearray(data))
    _transform(pIn, len(data))

    return bytes(pIn)

if __name__ == "__main__":
    import sys
    open(sys.argv[3], "wb").write(decompress(open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read()[:0x400000]))