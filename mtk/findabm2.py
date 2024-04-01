from formats import abm

if __name__ == '__main__':
    import sys    
    import struct
    import os

    f = bytearray(open(sys.argv[1], "rb").read())
    width, height = int(sys.argv[3]), int(sys.argv[4])
        
    count = 0
    match = f.find(struct.pack("<L", (height << 12) | width)[:3])

    #print(struct.pack("<L", (height << 12) | width)[:3])

    while match != -1:
        if (f[match+7] >> 4) & 7 != 1: 
            match = f.find(struct.pack("<L", (height << 12) | width)[:3], match+3)
            continue

        count += 1           

        try:
            abm.ab2Decode(f[match:match+0x100000]).save(f"{os.path.splitext(sys.argv[2])[0]}_{count}{os.path.splitext(sys.argv[2])[1]}")
            
        except Exception as e:
            print("error:",e)                
        
        match = f.find(struct.pack("<L", (height << 12) | width)[:3], match+3)