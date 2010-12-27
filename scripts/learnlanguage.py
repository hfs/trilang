#!/usr/bin/python3

import sys
from trilang import LanguageToken

def usage():
    print("""
Usage: python3 learnlanguage.py Language < file

    Language  - The name of the language
""")

def learnlanguage(text, language):
    lang = LanguageToken()
    lang.add_language(language)
    lang.train_text(text, language)

def main():
    if len(sys.argv) != 2 or sys.argv[1] in ['-h', '--help']:
        usage()
        return

    language = sys.argv[1]
    text = ''.join(sys.stdin)
    return learnlanguage(text, language)

if __name__ == "__main__":
    main()

