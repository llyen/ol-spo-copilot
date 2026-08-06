# -*- coding: utf-8 -*-
"""Jednorazowa poprawka: przywraca polskie znaki diakrytyczne w literalach
tekstowych plikow zrodlowych scenariusza.

Zamiana dotyczy wylacznie zawartosci literalow tekstowych - nazwy zmiennych,
klucze techniczne i kod pozostaja nietkniete. Slownik: corpus/pl_diacritics.py.

    python tools/apply_diacritics.py [--dry-run] plik.py ...
"""

from __future__ import annotations

import argparse
import io
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from corpus.pl_diacritics import restore  # noqa: E402

STRING_TOKENS = {tokenize.STRING}
if hasattr(tokenize, "FSTRING_MIDDLE"):
    STRING_TOKENS.add(tokenize.FSTRING_MIDDLE)


def process(source: str) -> tuple[str, int]:
    lines = source.splitlines(keepends=True)
    edits: list[tuple[int, int, int, int, str]] = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type not in STRING_TOKENS:
            continue
        fixed = restore(tok.string)
        if fixed != tok.string:
            edits.append((tok.start[0], tok.start[1], tok.end[0], tok.end[1], fixed))

    changed = 0
    for srow, scol, erow, ecol, fixed in reversed(edits):
        if srow != erow:
            head = lines[srow - 1][:scol]
            tail = lines[erow - 1][ecol:]
            lines[srow - 1 : erow] = [head + fixed + tail]
        else:
            line = lines[srow - 1]
            lines[srow - 1] = line[:scol] + fixed + line[ecol:]
        changed += 1
    return "".join(lines), changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for raw in args.paths:
        path = Path(raw)
        source = path.read_text(encoding="utf-8")
        fixed, changed = process(source)
        print(f"{path}: {changed} literalow poprawionych")
        if not args.dry_run and changed:
            path.write_text(fixed, encoding="utf-8")


if __name__ == "__main__":
    main()
