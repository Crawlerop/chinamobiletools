from formats import abm

if __name__ == '__main__':
    import sys    
    import struct
    import os

    f = bytearray(open(sys.argv[1], "rb").read())
    width, height = int(sys.argv[3]), int(sys.argv[4])
        
    count = 0
    match = f.find(struct.pack("<L", (width << 12) | (height & 0xff))[:3] + struct.pack("<HH", width, height))

    while match != -1:        
        count += 1           

        try:
            abm.ab1Decode(f[match+3:match+3+0x100000]).save(f"{os.path.splitext(sys.argv[2])[0]}_{count}{os.path.splitext(sys.argv[2])[1]}")
            
        except Exception as e:
            print("error:",e)                
        
        match = f.find(struct.pack("<L", (width << 12) | (height & 0xff))[:3] + struct.pack("<HH", width, height), match+7)