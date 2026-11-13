#!/bin/bash
# Pure Python: the tests of the data side and the syntax of the scripts.
set -euo pipefail
cd /project/apps/sfeed-hildon
for f in sfeed_hildon.py sfeed-hildon tests/make_demo.py; do
    python3 -I -c "import ast,sys; ast.parse(open('$f').read())"
done
python3 -I tests/test_sfeed_hildon.py > /tmp/sfeed-hildon-test.log || { cat /tmp/sfeed-hildon-test.log; exit 1; }
echo "sfeed-hildon: syntax ok, $(grep -c '^ok' /tmp/sfeed-hildon-test.log) tests passed"
