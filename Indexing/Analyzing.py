from abc import ABC
import definitions
import os
from whoosh.analysis import Analyzer, tokenizers, analyzers
from whoosh.analysis import LowercaseFilter, StopFilter, StemFilter
import regex as re

STOP_WORDS = list()
with open(os.path.join(definitions.MAIN_PATH, "Indexing", "STOP_WORDS_DE.txt"), encoding="utf-8") as f:
    for line in f.readlines():
        STOP_WORDS.append(line.strip())

with open(os.path.join(definitions.MAIN_PATH, "Indexing", "STOP_WORDS_EN.txt"), encoding="utf-8") as f:
    for line in f.readlines():
        STOP_WORDS.append(line.strip())


# Content analysis
class RegexTokenizer(tokenizers.RegexTokenizer):
    def __init__(self):
        super(RegexTokenizer, self).__init__()
        self.expression = re.compile(r"\p{L}{2,}", re.UNICODE)


def TextAnalyzer():
    chain = RegexTokenizer() | LowercaseFilter() | \
            StopFilter(stoplist=STOP_WORDS, minsize=2)
    return chain


# Heading analysis
class HeadingAnalyzer(Analyzer, ABC):
    pass


class SkillAnalyzer:
    pass
