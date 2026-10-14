"""Pair the user's supplied opening/ending translations by meaning, using only source row indices.

The original two-block files are preserved as *.provided.txt in the ignored lyrics folder.
No lyric text is embedded in this tool or in the movie specs.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# English indices are relative to the start of the user's English block.
MAPS = {
    'MOVIE003': (38, [
        [0], [0], [1], [1], [2], [2], [3, 4], [3, 4], [5], [6],
        [7], [8], [9], [10], [11], [12, 13], [12, 13], [14], [14],
        [15], [16], [17], [18], [19], [20], [21], [22], [23],
        [24], [25], [26], [27], [28], [29], [30], [31], [32], [33]
    ]),
    'MOVIE002': (21, [
        [0], [1], [2], [3, 4], [5], [6, 7], [8], [9], [10], [11],
        [12], [13, 14], [15], [16, 17], [18], [19], [20], [21],
        [22], [23, 24], [25, 26]
    ])
}


def main():
    folder = ROOT / 'work/translation/en/movies/lyrics'
    for movie, (split, mapping) in MAPS.items():
        path = folder / (movie + '.txt')
        original = folder / (movie + '.provided.txt')
        if not original.exists():
            assert not any('||' in r for r in path.read_text(encoding='utf-8-sig').splitlines()
                           if r.strip() and not r.lstrip().startswith('#'))
            original.write_bytes(path.read_bytes())
        rows = [s.strip() for s in original.read_text(encoding='utf-8-sig').splitlines()
                if s.strip() and not s.lstrip().startswith('#')]
        roma, english = rows[:split], rows[split:]
        assert len(roma) == len(mapping)
        assert set(i for m in mapping for i in m) == set(range(len(english)))
        paired = ['# User-supplied lyrics; meaning-matched pairs. Local only, excluded from git.']
        for r, indices in zip(roma, mapping):
            paired.append(r + ' || ' + ' '.join(english[i] for i in indices))
        path.write_text('\n'.join(paired) + '\n', encoding='utf-8')
        print(movie, len(roma), 'paired rows; original preserved')


if __name__ == '__main__':
    main()
