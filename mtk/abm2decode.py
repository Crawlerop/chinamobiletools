from formats import abm
import sys

if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    if len(sys.argv) >= 4:
        data = data[int(sys.argv[3], 16):]

    abm.ab2Decode(data).save(sys.argv[2])