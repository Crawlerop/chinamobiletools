import mido
import bitstring
import typing
import struct
import time

def _psleep(dur):
    ss = time.perf_counter()
    while time.perf_counter()<(ss+dur):
        pass

class CMIDI():
    def __init__(self, cmidi: typing.Union[str, bytes, bytearray]):
        if type(cmidi) == str:
            cmidi = open(cmidi, "rb").read()

        assert cmidi[:3] == b"MTK"
        self._timeRes, cmidiLen = struct.unpack(">BL", cmidi[3:8])
        self._cMidiBuf = bitstring.BitArray(cmidi[8:8+cmidiLen])
        self._cMidiPos = 0
        self._isEOF = False
        self._cNoteChannel = 0
        self._cNoteOctave = 0
        self._cNoteDeltaTime = 0
        
    def _getControl(self):
        if self._cMidiPos >= len(self._cMidiBuf): raise StopIteration()
        if self._cMidiBuf[self._cMidiPos]:
            if self._cMidiBuf[self._cMidiPos+1] and self._cMidiBuf[self._cMidiPos+2]:
                if self._cMidiBuf[self._cMidiPos+3]:
                    return 8, self._cMidiBuf[self._cMidiPos:self._cMidiPos+8]
                
                else:
                    return 5, self._cMidiBuf[self._cMidiPos:self._cMidiPos+5]
                
            else:
                return 3, self._cMidiBuf[self._cMidiPos:self._cMidiPos+3]
            
        else:
            return 2, self._cMidiBuf[self._cMidiPos:self._cMidiPos+2]

    def __iter__(self):
        return self

    def __next__(self):
        if self._isEOF: raise StopIteration()
        ret = None

        while not ret:
            controlSize, control = self._getControl()        

            self._cMidiPos += controlSize        
            if control.uint == 0xfa: # Bank LSB
                bank_lsb = self._cMidiBuf[self._cMidiPos:self._cMidiPos+7]
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=32, value=bank_lsb.uint)
                self._cMidiPos += 7

            elif control.uint == 0xf9: # DTime
                self._cNoteDeltaTime = self._cMidiBuf[self._cMidiPos:self._cMidiPos+10].uint + 1                       
                self._cMidiPos += 10

            elif control.uint == 0xf8: # Pitch sensitivity
                pitch_sens = self._cMidiBuf[self._cMidiPos:self._cMidiPos+7]
                ret = [mido.Message("control_change", channel=self._cNoteChannel, control=101, value=0), mido.Message("control_change", channel=self._cNoteChannel, control=100, value=0), mido.Message("control_change", channel=self._cNoteChannel, control=6, value=pitch_sens.uint)]                
                self._cMidiPos += 7

            elif control.uint == 0xf7: # Expression
                expression = self._cMidiBuf[self._cMidiPos:self._cMidiPos+5]
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=11, value=expression.uint << 2)
                self._cMidiPos += 5

            elif control.uint == 0xf6: # Modulation wheel
                modulation = self._cMidiBuf[self._cMidiPos:self._cMidiPos+7]
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=1, value=modulation.uint)
                self._cMidiPos += 7

            elif control.uint == 0xf5: # Bank MSB
                bank_msb = self._cMidiBuf[self._cMidiPos:self._cMidiPos+7]
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=0, value=bank_msb.uint)
                self._cMidiPos += 7

            elif control.uint == 0xf4: # Polytouch
                pitch = self._cMidiBuf[self._cMidiPos:self._cMidiPos+4]
                key_pressure = self._cMidiBuf[self._cMidiPos+4:self._cMidiPos+9]
                ret = mido.Message("polytouch", channel=self._cNoteChannel, note=(16*self._cNoteOctave)+pitch.uint, value=key_pressure.uint << 2)
                self._cMidiPos += 9

            elif control.uint == 0xf3: # Aftertouch
                channel_pressure = self._cMidiBuf[self._cMidiPos:self._cMidiPos+5]
                ret = mido.Message("aftertouch", channel=self._cNoteChannel, value=channel_pressure.uint << 2)
                self._cMidiPos += 5

            elif control.uint == 0xf2: # Program change
                program = self._cMidiBuf[self._cMidiPos:self._cMidiPos+7]
                ret = mido.Message("program_change", channel=self._cNoteChannel, program=program.uint)
                self._cMidiPos += 7

            elif control.uint == 0xf1: # Pan
                pan = self._cMidiBuf[self._cMidiPos:self._cMidiPos+5]
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=10, value=pan.uint << 2)
                self._cMidiPos += 5

            elif control.uint == 0xf0: # Sustain
                sustain = self._cMidiBuf[self._cMidiPos:self._cMidiPos+5]                                    
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=64, value=sustain.uint << 2)
                self._cMidiPos += 5

            elif control.uint == 0x1d: # Pitch bend
                pitch_wheel = self._cMidiBuf[self._cMidiPos:self._cMidiPos+7]            
                ret = mido.Message("pitchwheel", channel=self._cNoteChannel, pitch=pitch_wheel.uint)
                self._cMidiPos += 7

            elif control.uint == 0x1c: # Volume
                volume = self._cMidiBuf[self._cMidiPos:self._cMidiPos+5]
                ret = mido.Message("control_change", channel=self._cNoteChannel, control=7, value=volume.uint << 2)
                self._cMidiPos += 5

            elif control.uint == 0x6: # DTime
                self._cNoteDeltaTime = self._cMidiBuf[self._cMidiPos:self._cMidiPos+4].uint + 1                   
                self._cMidiPos += 4

            elif control.uint == 0x5: # Octave
                self._cNoteOctave = self._cMidiBuf[self._cMidiPos:self._cMidiPos+3].uint
                self._cMidiPos += 3

            elif control.uint == 0x4: # Channel
                self._cNoteChannel = self._cMidiBuf[self._cMidiPos:self._cMidiPos+4].uint
                self._cMidiPos += 4

            elif control.uint == 0x1: # Note off
                pitch = self._cMidiBuf[self._cMidiPos:self._cMidiPos+4]     
                ret = mido.Message("note_off", channel=self._cNoteChannel, note=(16*self._cNoteOctave)+pitch.uint)
                self._cMidiPos += 4

            elif control.uint == 0x0: # Note on
                pitch = self._cMidiBuf[self._cMidiPos:self._cMidiPos+4]
                velocity = self._cMidiBuf[self._cMidiPos+4:self._cMidiPos+9]            
                if pitch.length < 4 or velocity.length < 5: # EOF
                    self._isEOF = True
                    raise StopIteration() 
                
                ret = mido.Message("note_on", channel=self._cNoteChannel, note=(16*self._cNoteOctave)+pitch.uint, velocity=velocity.uint << 2)

                self._cMidiPos += 9

            else:
                raise Exception(hex(control.uint))                        
        
        pDeltaTime = self._cNoteDeltaTime
        self._cNoteDeltaTime = 0
        
        return pDeltaTime * self._timeRes, ret
    
    def play(self):
        for (delta, track) in self.__iter__():
            _psleep(delta / 1000)
            yield track