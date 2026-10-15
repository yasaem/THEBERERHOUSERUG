"""Shared French/English interface and API message catalogue.

Business data and historical invoice amounts are never translated here.
"""
import json
import re
from pathlib import Path

EN = json.loads((Path(__file__).parent / 'static' / 'translations.json').read_text())
PATTERN = re.compile(r'(?<![\w])(' + '|'.join(re.escape(k) for k in sorted(EN, key=len, reverse=True)) + r')(?![\w])')

def language(value):
    if value not in ('fr', 'en'):
        raise ValueError('Langue non prise en charge')
    return value

def translate(text, selected='fr'):
    if selected != 'en':
        return str(text)
    text = str(text)
    if text in EN:
        return EN[text]
    # Error suffixes can contain product names/references: keep them literal.
    head, separator, suffix = text.partition(': ')
    if separator and head in EN:
        return EN[head] + separator + suffix
    return PATTERN.sub(lambda match: EN[match.group()], text)
