"""Text -> index terms. Documents and queries must go through the same function."""

import re
import unicodedata

import Stemmer

_stemmer = Stemmer.Stemmer("english")

# SPlit on punctation/hyphens, but not things like decimals
TOKEN = re.compile(r"\d+(?:\.\d+)+|[^\W_]+")
POSSESSIVE = re.compile(r"['’]s\b")

# Remove common words
HEADWORDS = frozenset(
    """
    a about above after again against all also am an and any are as at be because been
    before being below between both but by can could did do does doing down during each
    few for from further had has have having he her here hers herself him himself his how
    i if in into is it its itself just me more most my myself no nor not of off on once
    only or other our ours ourselves out over own same she should so some such than that
    the their theirs them themselves then there these they this those through to too under
    until up very was we were what when where which while who whom why will with would you
    your yours yourself yourselves
    """.split()
)


def fold(text: str) -> str:
    """Lowercase and get rid of accents but not greek letters (for things like \beta)"""
    text = text.casefold()
    if text.isascii():
        return text
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def tokenize(text: str, stem: bool = True) -> list[str]:
    text = POSSESSIVE.sub("", fold(text))
    tokens = [t for t in TOKEN.findall(text) if t not in HEADWORDS]
    return _stemmer.stemWords(tokens) if stem else tokens
