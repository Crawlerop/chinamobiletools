import vmsplitter

if __name__ == '__main__':
    import sys 
    import os

    f = bytearray(open(sys.argv[1], "rb").read())    
        
    count = 0
    match = f.find(b"VM")

    while match != -1:
        if f[match+0xe:match+0x12] == b"\x28\x00\x00\x00":
            count += 1                
            fsize = int.from_bytes(f[match+2:match+6], "little")
            print(fsize, f[match:match+8], hex(match))

            try:
                for i, t in enumerate(vmsplitter.load_vm(f[match:match+fsize])):
                    open(f"{os.path.splitext(sys.argv[2])[0]}_{count}_{i+1:04d}{os.path.splitext(sys.argv[2])[1]}", "wb").write(t)
                
            except Exception as e:                
                print("error:",e)                        
                pass

        match = f.find(b"VM", match+2)