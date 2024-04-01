from formats import cmidi
import mido
import sys

if __name__ == "__main__":
    m = mido.open_output()
    
    cmi = None

    if len(sys.argv) >= 4:
        cmi = cmidi.CMIDI(open(sys.argv[1], "rb").read()[int(sys.argv[3], 16):])
        
    else:
        cmi = cmidi.CMIDI(sys.argv[1])

    mFile: mido.MidiFile = mido.MidiFile(type=0)
    mTrack: mido.MidiTrack = mido.MidiTrack()
    
    mFile.tracks.append(mTrack)    
    mTrack.append(mido.MetaMessage("set_tempo", tempo=480000))
    
    for (delay, message) in cmi:        
        if type(message) == list:
            message[0].time = delay
            for ms2 in message:
                mTrack.append(ms2)

        else:
            message.time = delay
            mTrack.append(message)

    mFile.save(sys.argv[2])