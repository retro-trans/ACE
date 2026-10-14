"""Read user-supplied, local-only karaoke lyrics without imaging dependencies."""
import re
from pathlib import Path


def read_lyrics(path):
    rows = [r.strip() for r in Path(path).read_text(encoding='utf-8-sig').splitlines()]
    rows = [r for r in rows if r and not r.startswith('#')]
    if any('||' in r for r in rows):
        out, last = [], None
        for row in rows:
            if '||' not in row:
                raise ValueError('Mixed paired/unpaired lyric rows: ' + str(path))
            roma, _, english = row.partition('||')
            if english.strip():
                last = english.strip()
            out.append((roma.strip(), last))
        return out
    common = set('the a an and of to my your you i in on is it its with like for that this when if will be me at '
                 'by from are am our we'.split())

    def english_like(row):
        words = re.findall(r"[a-z']+", row.lower())
        return not re.search(r'[^\x00-\x7f]', row) and words and sum(w in common for w in words) / len(words) > .2

    k = next((i for i, row in enumerate(rows) if english_like(row)), len(rows))
    roma, english = rows[:k], rows[k:]
    if english:
        raise ValueError('Two-block lyrics must be paired by meaning before rendering: ' + str(path))
    return [(r, None) for r in roma]
