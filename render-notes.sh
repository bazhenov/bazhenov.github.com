#!/usr/bin/env bash
set -e

for F in content/notes/*.md; do
    if [[ "${F: -10}" != "/_index.md" ]]; then
        echo "Removing $F"
        rm "$F"
    fi
done

python3 logseq-export.py render-all ~/logseq ./content/notes
