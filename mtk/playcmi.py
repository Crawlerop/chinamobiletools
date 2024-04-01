from formats import cmidi
import mido
import sys

if __name__ == "__main__":
    m = mido.open_output()
    
    cmi = None

    if len(sys.argv) >= 3:
        cmi = cmidi.CMIDI(open(sys.argv[1], "rb").read()[int(sys.argv[2], 16):])
        
    else:
        cmi = cmidi.CMIDI(sys.argv[1])
    
    for message in cmi.play():
        if type(message) == list:
            for ms2 in message:
                m.send(ms2)    
        else:
            m.send(message)    