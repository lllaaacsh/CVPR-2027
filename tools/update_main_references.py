#!/usr/bin/env python3
"""Refresh standalone supplementary references after compiling main.tex.

Usage: python tools/update_main_references.py path/to/main.aux
The committed snapshot lets Overleaf compile supp.tex independently of main.tex.
"""

import argparse
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('main_aux', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    snapshot = root / 'supp/main_references.tex'
    current = snapshot.read_text()
    labels = re.findall(r'\\DeclareMainReference\{([^}]+)\}', current)
    records = dict(re.findall(r'^\\newlabel\{([^}]+)\}(.*)$', args.main_aux.read_text(), re.M))
    lines = [line for line in current.splitlines() if line.startswith('%')]
    for label in labels:
        if label not in records:
            raise ValueError(f'Main-paper label missing: {label}')
        number = re.match(r'\{\{([^}]*)\}', records[label])[1]
        kind = re.match(r'\{\{\[([^]]+)\]', records[label + '@cref'])[1]
        kind = {'subtable': 'table'}.get(kind, kind)
        display = '(' + number + ')' if kind == 'equation' else number
        if kind in {'equation', 'figure', 'table'}:
            kind = kind.capitalize()
        lines.append('\\DeclareMainReference{' + label + '}{' + kind + '~' + display
                     + '}{' + kind.capitalize() + '~' + display + '}')
    snapshot.write_text('\n'.join(lines) + '\n')
    print(f'Updated {len(labels)} main-paper references in {snapshot}')


if __name__ == '__main__':
    main()
