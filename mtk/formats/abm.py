import struct
import bitstring
from PIL import Image
import typing
import os

def get_need_bits(p):
    bits = 0
    while p != 0:        
        bits += 1
        p >>= 1
    
    return bits

def ab1Decode(img: typing.Union[bytes, bytearray]):
    img = bytes(img)
    width, height, noPalettes, noAlphaPalettes, w_tl, h_tl, w_br, h_br = struct.unpack("<HHHHBBBB", img[:0xc])

    isFullyOpaque = width >> 15
    is24Bit = height >> 15

    width &= 0x7fff
    height &= 0x7fff    

    noPalettes -= 1

    palettes = [b"\xff\x00\xff" if is24Bit else b"\x1f\xf8"]    
    alphas = []

    offset = 0xc

    for _ in range(noPalettes+noAlphaPalettes):
        palettes.append(img[offset:offset+(3 if is24Bit else 2)])
        offset += 3 if is24Bit else 2        

    for _ in range(noAlphaPalettes):
        alphas.append(img[offset])
        offset += 1    
    
    if offset & 1:
        offset += 1
    
    bImg = bitstring.BitArray(img[offset:(offset+(width*height*4))])

    aOffset = 0
    bOffset = 0

    def read_bits(p):
        nonlocal aOffset, bOffset
        if (aOffset*8) >= bImg.length: return 0

        temp = 0
        for cc in range(p):
            ba = bImg[(aOffset*8)+(7-bOffset)]            

            bOffset += 1
            if bOffset >= 8:            
                bOffset = 0
                aOffset += 1                
                if (aOffset*8) >= bImg.length:                    
                    temp |= (ba << cc)
                    return temp

            temp |= (ba << cc)
        
        return temp
    
    total = 1 + noPalettes + noAlphaPalettes  
    
    outBuf = bytearray()
    alphaBuf = bytearray()

    crop_w = width - (w_tl + w_br)
    crop_h = height - (h_tl + h_br)

    while len(outBuf)<(crop_w * crop_h) * (3 if is24Bit else 2):
        p = read_bits(get_need_bits(total-1))              
        if p < len(palettes):
            if p >= (noPalettes + 1):                            
                outBuf += palettes[p]                
                alphaBuf.append(alphas[p - (noPalettes + 1)] ^ 0xff)

            else:
                outBuf += palettes[p]
                alphaBuf.append(0xff if p > 0 or isFullyOpaque else 0x0)
            
    temp = Image.frombytes("RGB", (crop_w, crop_h), bytes(outBuf)).convert("RGBA") if is24Bit else Image.frombytes("RGB", (crop_w, crop_h), bytes(outBuf), "raw", "BGR;16", 0, 1).convert("RGBA")
    temp.putalpha(Image.frombytes("L", (crop_w, crop_h), bytes(alphaBuf)))        
            
    out = Image.new("RGBA", (width, height))
    out.paste(temp, (w_tl, h_tl, width-w_br, height-h_br))

    return out

def ab2Decode(img: typing.Union[bytes, bytearray], use_predef_palette=False):
    img = bytes(img)
    _f1, _f2, noPalettes, noAlphaPalettes = struct.unpack("<LLHH", img[:0xc])
    
    width = _f1 & 0xfff
    height = (_f1 >> 12) & 0xfff

    w_tl = _f1 >> 24
    h_tl = _f2 & 0xff

    w_br = (_f2 >> 8) & 0xff
    h_br = (_f2 >> 16) & 0xff

    pixFormat = (_f2 >> 24) & 0xf
    assert ((_f2 >> 28) & 0x7) == 1

    is24Bit = (pixFormat & 1) == 0    
    
    palettes = [] if use_predef_palette else [b"\xff\x00\xff" if is24Bit else b"\x1f\xf8"]    
    alphas = []

    offset = 0xc if not use_predef_palette else 0x8

    if not use_predef_palette:
        for _ in range(noPalettes):
            palettes.append(img[offset:offset+(3 if is24Bit else 2)])
            offset += 3 if is24Bit else 2        

        if offset & 1:
            offset += 1

        for _ in range(noAlphaPalettes):
            palettes.append(img[offset:offset+(3 if is24Bit else 2)])
            alphas.append(img[offset+(3 if is24Bit else 2):offset+(4 if is24Bit else 3)][0])
            offset += 4 if is24Bit else 3   
        
        if offset & 1:
            offset += 1

    else:
        noPalettes = 255
        noAlphaPalettes = 0x0
        is24Bit = True

        _pdPalFile = open(os.path.join(os.path.dirname(__file__), "abm-pal.bin"), "rb")
        
        _pdPalCol = _pdPalFile.read(3)

        while _pdPalCol:
            palettes.append(_pdPalCol)
            _pdPalCol = _pdPalFile.read(3)
                
    
    bImg = bitstring.BitArray(img[offset:(offset+(width*height*4))])    

    aOffset = 0
    bOffset = 0

    def read_bits(p):
        nonlocal aOffset, bOffset
        if (aOffset*8) >= bImg.length: return 0

        temp = 0
        for cc in range(p):
            ba = bImg[(aOffset*8)+(7-bOffset)]            

            bOffset += 1
            if bOffset >= 8:            
                bOffset = 0
                aOffset += 1                
                if (aOffset*8) >= bImg.length:                    
                    temp |= (ba << cc)
                    return temp

            temp |= (ba << cc)
        
        return temp
    
    total = 1 + noPalettes + noAlphaPalettes  
    
    outBuf = bytearray()
    alphaBuf = bytearray()

    crop_w = width - (w_tl + w_br)
    crop_h = height - (h_tl + h_br)
        
    while len(outBuf)<(crop_w * crop_h) * (3 if is24Bit else 2):
        flag = read_bits(8)        

        if flag < 0x80:
            count = flag + 1
            pix = read_bits(get_need_bits(total-1))            

            for _ in range(count):
                if pix < len(palettes):
                    if pix >= (noPalettes + 1):                            
                        outBuf += palettes[pix]                
                        alphaBuf.append(alphas[pix - (noPalettes + 1)] ^ 0xff)

                    else:
                        outBuf += palettes[pix]
                        alphaBuf.append(0xff if pix > 0 or (pixFormat & 4) else 0x0)
            
        else:
            count = flag - 0x7f
            for _ in range(count):
                pix = read_bits(get_need_bits(total-1))

                if pix < len(palettes):
                    if pix >= (noPalettes + 1):                            
                        outBuf += palettes[pix]                
                        alphaBuf.append(alphas[pix - (noPalettes + 1)] ^ 0xff)

                    else:
                        outBuf += palettes[pix]
                        alphaBuf.append(0xff if pix > 0 or (pixFormat & 4) else 0x0)
            
    temp = Image.frombytes("RGB", (crop_w, crop_h), bytes(outBuf)).convert("RGBA") if is24Bit else Image.frombytes("RGB", (crop_w, crop_h), bytes(outBuf), "raw", "BGR;16", 0, 1).convert("RGBA")
    temp.putalpha(Image.frombytes("L", (crop_w, crop_h), bytes(alphaBuf)))        
        
    out = Image.new("RGBA", (width, height))
    out.paste(temp, (w_tl, h_tl, width-w_br, height-h_br))

    return out