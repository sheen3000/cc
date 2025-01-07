'''
Common functions
'''

import re

re_text_only = re.compile(r'[^a-z0-9 .-]')


def normalize_text_for_embedding(text: str) -> str:
    # TODO: verify we don't want more characters (comma? dot?)... , stemming, lemmatization, handling contractions, and removing accents
    text = text.lower()
    text = re_text_only.sub('', text)
    return text

