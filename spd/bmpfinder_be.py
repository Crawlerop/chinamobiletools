import bmpconverter

if __name__ == '__main__':
    import sys     
    import os

    f = bytearray(open(sys.argv[1], "rb").read())
    #width, height = int(sys.argv[3]), int(sys.argv[4])
        
    count = 0
    match = f.find(b"MB")

    while match != -1:
        if f[match+0xe:match+0x12] == b"\x00\x00\x00\x28":
            count += 1                
            fsize = int.from_bytes(f[match+2:match+6], "big")
            print(fsize, f[match:match+8], hex(match))

            try:
                t = bmpconverter.translate_bmp_big(f[match:match+fsize])
                open(f"{os.path.splitext(sys.argv[2])[0]}_{count}{os.path.splitext(sys.argv[2])[1]}", "wb").write(t)
            except Exception as e:                
                print("error:",e)                        
                pass

        match = f.find(b"MB", match+2)