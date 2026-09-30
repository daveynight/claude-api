"""Git clean filter: strip outputs from a notebook so only code is committed.

Reads a notebook on stdin and writes the stripped notebook to stdout. Git runs
this on the staged copy only, so outputs stay in the working file.
"""
import sys

import nbformat

nb = nbformat.read(sys.stdin, as_version=4)

for cell in nb.cells:
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

nbformat.write(nb, sys.stdout)
