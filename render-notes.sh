#!/usr/bin/env bash

for F in content/notes/*.md; do
    if [[ "${F: -10}" != "/_index.md" ]]; then
        rm -f $F
    fi
done

python3 logseq-export.py render-all ~/logseq ./content/notes
