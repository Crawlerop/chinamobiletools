import sys    
import struct
import os
import io
from PIL import Image

def decompress(data):
    data = io.BytesIO(data)

    assert data.read(3) == b"ABM"
    imgType = data.read(1)[0]

    assert imgType in [0x50, 0x52]

    width, height, noColor, noAlpha, topY, topX, bottomY, bottomX = struct.unpack(">HHHHBBBB", data.read(0xc))    
    noColors = noColor + noAlpha

    actualWidth = width - bottomX - topX
    actualHeight = height - bottomY - topY
    #print(actualWidth, actualHeight, width, height)

    pData = [b"\xf8\x1f"] + [data.read(2) for _ in range(noColors-1)]      
    pAlpha = [0] + ([0xff] * (noColor-1)) + [x for x in data.read(noAlpha)]    

    if noAlpha & 1:
        data.read(1)

    ncTemp = noColors - 1
    bpp = 0

    while ncTemp != 0:
        bpp += 1
        ncTemp >>= 1        

    cmp_len = 0
    if imgType == 0x52:
        cmp_len = int.from_bytes(data.read(4), "little")    

    cmp_data = data.read(cmp_len)
    cmp_offs = 0

    next = 0x10000 | int.from_bytes(data.read(2), "big" if imgType == 0x50 else "little")        

    def read_bits(p):
        nonlocal next
        temp = 0
        for k in range(p):                        
            temp |= ((next & 1) << k)                        
            next >>= 1
            
            if next == 1:
                next = 0x10000 | int.from_bytes(data.read(2), "big" if imgType == 0x50 else "little")

        return temp
            
    tempData = bytearray()
    tempAlpha = bytearray()

    while len(tempData) < ((actualWidth * actualHeight) * (2 if noColors > 0x100 else 1)): 
        pixels = 1
        count = 0

        if imgType == 0x52:
            pixels, count = struct.unpack("<BB", cmp_data[cmp_offs:cmp_offs+2])
            cmp_offs += 2

            if pixels <= 0 and count <= 0: continue

        for _ in range(pixels):
            pix = read_bits(bpp)
            assert pix < noColors, f"pix: {pix}, col: {noColors}"

            if noColors > 0x100:
                tempData += (pData[pix][1:2] + pData[pix][0:1])
                tempAlpha += pAlpha[pix].to_bytes(1, "little")                    

            else:
                tempData += pix.to_bytes(1, "little")

        if count > 0:
            pix = read_bits(bpp)
            assert pix < noColors, f"pix: {pix}, col: {noColors}"           

            if noColors > 0x100:
                tempData += (pData[pix][1:2] + pData[pix][0:1]) * count
                tempAlpha += pAlpha[pix].to_bytes(1, "little") * count

            else:
                tempData += pix.to_bytes(1, "little") * count

    if noColors > 0x100:        
        temp = Image.frombytes("RGB", (actualWidth, actualHeight), tempData, "raw", "BGR;16", 0, 1)
        tempOut = Image.new("RGBA", (width, height))
        tempOut.paste(temp, (topX, bottomX), Image.frombytes("L", (actualWidth, actualHeight), tempAlpha))

        return tempOut, []
    
    else:        
        temp = Image.frombytes("P", (actualWidth, actualHeight), tempData)
        temp.putpalette(b"".join([(x[1:2] + x[0:1]) for x in pData]), "BGR;16")

        tempOut = Image.new("P", (width, height))
        tempOut.putpalette(b"".join([(x[1:2] + x[0:1]) for x in pData]), "BGR;16")

        tempOut.paste(temp, (topX, bottomX))
        return temp, pAlpha
            

if __name__ == "__main__":
    import sys
    decompress(open(sys.argv[1], "rb").read())[0].save(sys.argv[2])