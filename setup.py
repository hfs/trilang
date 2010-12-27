from distutils.core import setup
setup(
    name = 'trilang',
    version = '0.1',
    url = 'http://github.com/hfs/trilang',
    description = 'Statistical language detector',
    long_description = """\
trilang is a statistical language detector. To detect the language of a \
text it divides it into trigrams (blocks of three letters) and compares \
their frequency with reference values in its database. The database is \
initially empty and has to be filled by learning from texts with known \
languages.""",
    author = 'Hermann Schwarting',
    author_email = 'trilang@knackich.de',
    py_modules = ['trilang'],
    scripts = [
        'scripts/correctlanguage.py',
        'scripts/guesslanguage.py',
        'scripts/learnlanguage.py',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
    ],
    requires = ['sqlite3'],
)

