#!/usr/bin/python3

import sys
from trilang import Classifier

def usage():
    print("Usage: python3 guesslanguage.py < file")

def main():
    c = Classifier()
    text = ''.join(sys.stdin)
    print(c.classify(text))

if __name__ == "__main__":
    if len(sys.argv) != 1:
        usage()
    else:
        main()
