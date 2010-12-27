#!/usr/bin/python3
"""
trilang -- statistical language detector

trilang is a statistical language detector. To detect the language of a text it
divides it into trigrams (blocks of three letters) and compares their frequency
with reference values in its database. The database is initially empty and has
to be filled by learning from texts with known languages.

The statistical approach has been described in the article "A Statistical
Approach to the Spam Problem" by Gary Robinson, 1 Mar 2003, Linux Journal,
http://www.linuxjournal.com/article/6467 .

"""
import math
import operator
import re
import sqlite3 as db

class Token(object):

    types = []
    default_type = 'default'

    def __init__(self, filename, length=3):
        self.connection = db.connect(filename)
        cursor = self.connection.cursor()
        cursor.execute("""
                PRAGMA synchronous=OFF;
                """)
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS token (
                id TEXT(%i) PRIMARY KEY,
                "%s" INTEGER DEFAULT 0 CHECK ("%s" >= 0));
            """ % (length, self.default_type, self.default_type))
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS type (
                id TEXT PRIMARY KEY
                );""")
        cursor.execute("""
                CREATE TABLE IF NOT EXISTS totals (
                "%s" INTEGER DEFAULT 0
                );""" % (self.default_type,))
        cursor.execute("SELECT * FROM totals")
        totals = cursor.fetchall()
        if (len(totals) == 0):
            cursor.execute("INSERT INTO totals DEFAULT VALUES;")
        cursor.execute("INSERT OR IGNORE INTO type VALUES (?);",
                (self.default_type,))
        cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS token_insert_sum
                AFTER INSERT ON token FOR EACH ROW BEGIN
                UPDATE totals SET
                "%s" = "%s" + NEW."%s";
                END;""" % ((self.default_type,) * 3))
        cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS token_update_sum
                AFTER UPDATE ON token FOR EACH ROW BEGIN
                UPDATE totals SET
                "%s" = "%s" - OLD."%s" + NEW."%s";
                END;""" % ((self.default_type,) * 4))
        cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS token_delete_sum
                AFTER DELETE ON token FOR EACH ROW BEGIN
                UPDATE totals SET
                "%s" = "%s" - OLD."%s";
                END;""" % ((self.default_type,) * 3))
        cursor.execute("INSERT OR IGNORE " +
                "INTO token(id, \"%s\") " % self.default_type +
                "VALUES ('   ', 1);")
        self.connection.commit()
        cursor.execute("SELECT * FROM type;")
        self.types = [each[0] for each in cursor.fetchall()]
        cursor.close()

    def get_counts(self, tokens):
        result = []
        multi = {} # multiplicity per token
        for token in tokens:
            if token in multi:
                multi[token] += 1
            else:
                multi[token] = 1
        empty = (0,) * len(self.types)
        cursor = self.connection.cursor()
        existing = 0
        for token in multi.keys():
            cursor.execute('SELECT "id","%s" FROM token WHERE id = ?;' % (
                    '","'.join(self.types),),
                    (token,))
            row = cursor.fetchone()
            if row is not None:
                id = row[0]
                counts = row[1:]
                result.extend([counts] * multi[id])
                existing += multi[id]
        cursor.close()
        # append null tuples for inexistent tokens
        result.extend([empty] * (len(tokens) - existing))
        return (self.types, result) 

    def totals(self):
        cursor = self.connection.cursor()
        cursor.execute('SELECT "%s" FROM totals;' %
                '","'.join(self.types))
        return cursor.fetchone()

    def train_token(self, tokens, type):
        if len(tokens) == 0:
            return
        cursor = self.connection.cursor()
        for token in tokens:
            # insert new tokens
            cursor.execute('INSERT OR IGNORE INTO token(id) VALUES (?);',
                    (token,))
            # update existing tokens
            cursor.execute('UPDATE token SET "%s" = "%s" + 1 ' % (type, type) +
                    'WHERE id = ?;', (token,))
        self.connection.commit()
        cursor.close()

    def correct_token(self, tokens, fromType, toType):
        if len(tokens) == 0:
            return
        cursor = self.connection.cursor()
        for token in tokens:
            cursor.execute('UPDATE token SET ' +
                '"%s"="%s"-1, "%s"="%s"+1 ' % (fromType, fromType, toType, toType) +
                'WHERE id = ?', (token,))
        self.connection.commit()
        cursor.close()

    def add_type(self, name):
        if name in self.types:
            return
        cursor = self.connection.cursor()
        cursor.execute("""
                ALTER TABLE token ADD COLUMN
                "%s" INTEGER DEFAULT 0 CHECK ("%s" >= 0);
                """ % (name, name))
        cursor.execute("""
                ALTER TABLE totals ADD COLUMN
                "%s" INTEGER DEFAULT 0
                """ % (name,))
        cursor.execute('INSERT INTO type VALUES (?)', (name,))
        cursor.execute("DROP TRIGGER token_insert_sum;")
        cursor.execute("DROP TRIGGER token_update_sum;")
        cursor.execute("DROP TRIGGER token_delete_sum;")
        cursor.execute("""
                CREATE TRIGGER token_insert_sum
                AFTER INSERT ON token FOR EACH ROW BEGIN
                UPDATE totals SET """ +
                ",\n".join(['"%s" = "%s" + NEW."%s"' % ((each,)*3) for each in self.types + [name]]) +
                ";\nEND;")
        cursor.execute("""
                CREATE TRIGGER token_update_sum
                AFTER UPDATE ON token FOR EACH ROW BEGIN
                UPDATE totals SET """ +
                ",\n".join(['"%s" = "%s" - OLD."%s" + NEW."%s"' % ((each,)*4) for each in self.types + [name]]) +
                ";\nEND;")
        cursor.execute("""
                CREATE TRIGGER token_delete_sum
                AFTER DELETE ON token FOR EACH ROW BEGIN
                UPDATE totals SET """ +
                ",\n".join(['"%s" = "%s" - OLD."%s"' % ((each,)*3) for each in self.types + [name]]) +
                ";\nEND;")
        cursor.execute("UPDATE token SET \"%s\" = 1 WHERE id = '   ';" % name)
        self.connection.commit()
        self.types.append(name)
        cursor.close()

class LanguageToken(Token):

    default_type = 'English'

    def __init__(self, filename='trilang.db'):
       Token.__init__(self, filename, length=3)

    def get_counts_for_text(self, text):
        text = clean(text)
        token = trigrams(text)
        return Token.get_counts(self, token)

    def train_text(self, text, language):
        text = clean(text)
        token = trigrams(text)
        return Token.train_token(self, token, language)

    def correct_text(self, text, fromLanguage, toLanguage):
        text = clean(text)
        token = trigrams(text)
        return Token.correct_token(self, token, fromLanguage, toLanguage)

    def add_language(*args, **kw):
        Token.add_type(*args, **kw)

def clean(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^\s*', '  ', text)
    text = re.sub(r'\s*$', '  ', text)
    return text

def trigrams(text):
    return [ text[i:i+3] for i in range(0, len(text)-2) ]

class Classifier(object):

    lang = LanguageToken()

    def classify(self, text):
        lang2score = self.classify_per_language(text)
        return select_winner(lang2score)

    def classify_per_language(self, text):
        defaultProb = 0.5
        defaultWeight = 1

        (languages, counts) = self.lang.get_counts_for_text(text)
        n = len(languages)
        # Total count per language
        totals = self.lang.totals()
        # Totals of all other languages, per language
        totalsOthers = list(map(operator.sub, (sum(totals),) * n, totals))

        # The current total probability, in the order of languages
        prob = [0.0] * n
        prob1m = [0.0] * n # "1 - prob"

        for count in counts:
            freq = sum(count)
            if freq == 0:
                for i in range(n):
                    prob[i] += math.log(defaultProb)
                    prob1m[i] += math.log(1 - defaultProb)
            else:
                for i in range(n):
                    countOthers = freq - count[i]
                    support = float(count[i]) / float(totals[i])
                    refusal = float(countOthers) / float(totalsOthers[i])
                    plaus = support / (support + refusal)
                    plaus = ( defaultWeight * defaultProb + freq * plaus ) / (defaultWeight + freq )
                    prob[i] += math.log(plaus)
                    prob1m[i] += math.log( 1 - plaus )

        totalSupport = [chi2P(-2 * prob[i], 2 * len(counts)) for i in range(n)]
        totalRefusal = [chi2P(-2 * prob1m[i], 2 * len(counts)) for i in range(n)]
        result = [(1 + totalSupport[i] - totalRefusal[i]) / 2 for i in range(n)]
        return dict(zip(languages, result))

def select_winner(scores):
    """From a dict of categories => scores [0,1] select a winner. One category
    must have score above a threshold, all others must be below a second
    threshold.  Else None is returned."""
    win_threshold = 0.9
    lose_threshold = 0.5
    n = len(scores)
    winners = list(filter(lambda x: x[1] > win_threshold, scores.items()))
    losers = list(filter(lambda x: x[1] <= lose_threshold, scores.items()))
    if len(winners) != 1 or len(losers) != n - 1:
        return None
    else:
        return winners[0][0]

def chi2P(chi, df):
    """Return prob(chisq >= chi, with df degrees of freedom).
    df must be even.
    """
    assert df & 1 == 0
    # XXX If chi is very large, exp(-m) will underflow to 0.
    m = chi / 2.0
    sum = term = math.exp(-m)
    for i in range(1, df//2):
        term *= m / i
        sum += term
    # With small chi and large df, accumulated
    # roundoff error, plus error in
    # the platform exp(), can cause this to spill
    # a few ULP above 1.0. For
    # example, chi2P(100, 300) on my box
    # has sum == 1.0 + 2.0**-52 at this
    # point.  Returning a value even a teensy 
    # bit over 1.0 is no good.
    return min(sum, 1.0)

