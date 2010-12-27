#!/usr/bin/python3

import sys
from trilang import LanguageToken

def usage():
    print("""
Usage: python correctlanguage.py From-Language To-Language < file
""")

def correctlanguage(text, fromlang, tolang):
    lang = LanguageToken()
    lang.correct_text(text, fromlang, tolang)

def main():
    if len(sys.argv) != 3 or sys.argv[0] in ['-h', '--help']:
        usage()
    else:
        text = ''.join(sys.stdin)
        correctlanguage(text, sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()

