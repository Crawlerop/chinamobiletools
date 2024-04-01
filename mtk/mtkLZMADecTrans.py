from mtklzma import mtklzma
import sys

if __name__ == "__main__":
    inFile = open(sys.argv[1], "rb").read()
    outFile = open(sys.argv[2], "wb")

    if len(sys.argv) >= 4:        
        inFile = inFile[int(sys.argv[3], 16):]

    outFile.write(mtklzma.transformProcess(mtklzma.decompress(inFile)))