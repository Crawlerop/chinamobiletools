import sprd_abm

if __name__ == '__main__':
    import sys
    import struct        
    import os

    f = bytearray(open(sys.argv[1], "rb").read())
    #width, height = int(sys.argv[3]), int(sys.argv[4])
        
    count = 0
    match = f.find(b"ABMP")

    while match != -1:
        count += 1                
        try:
            print(hex(match))
            width, height = struct.unpack(">HH", f[match+4:match+8])
            print(width, height)
            img, mask = sprd_abm.decompress(f[match:match+0x400000])                    

            if len(mask) <= 0:
                img.save(f"{os.path.splitext(sys.argv[2])[0]}_{count}_r_{width}_{height}{os.path.splitext(sys.argv[2])[1]}")
            else:
                img.save(f"{os.path.splitext(sys.argv[2])[0]}_{count}_r_{width}_{height}{os.path.splitext(sys.argv[2])[1]}", transparency=bytes(mask))
        except Exception as e:
            print("error:",e)                        
            pass
        match = f.find(b"ABMP", match+4)

    count = 0
    match = f.find(b"ABMR")

    while match != -1:
        count += 1                
        try:
            print(hex(match))
            width, height = struct.unpack(">HH", f[match+4:match+8])
            print(width, height)
            img, mask = sprd_abm.decompress(f[match:match+0x400000])                                

            if len(mask) <= 0:
                img.save(f"{os.path.splitext(sys.argv[2])[0]}_{count}_r_{width}_{height}{os.path.splitext(sys.argv[2])[1]}")
            else:
                img.save(f"{os.path.splitext(sys.argv[2])[0]}_{count}_r_{width}_{height}{os.path.splitext(sys.argv[2])[1]}", transparency=bytes(mask))
        except Exception as e:
            print("error:",e)                        
            pass
        match = f.find(b"ABMR", match+4)        

    