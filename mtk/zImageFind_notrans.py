from formats import gfh, viva
import sys
import os
from mtklzma import mtklzma

if __name__ == "__main__":    
    zImageDict = open(sys.argv[2], "rb").read()[:0x400000]
    gfs = gfh.findGFH(open(sys.argv[1], "rb").read())
    for f in gfs:
        fileinfo, filedata = f
        if fileinfo.info_type == 0x108:
            vivaHead = viva.VIVA.parse(filedata[fileinfo.info_content_offset:])    
            
            zImage = viva.zPartition.parse(filedata[vivaHead.zimage:])           
            
            fOut = open(sys.argv[3], "wb")            

            for part in zImage.partitions:            
                if part.compression_type == 3: # 3 = LZMA with Train from ALICE
                    fOut.write(mtklzma.decompress(part.data, zImageDict))
                else: # 0 = LZMA, 1 = LZMA with callback, 2 = Same as 0
                    fOut.write(mtklzma.decompress(part.data))
