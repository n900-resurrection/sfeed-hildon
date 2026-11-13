# Name: Feeds (sfeed-hildon)
# Sourced by scripts/hildon-run.sh (INSIDE the Workshop) for: make hildon-run APP=sfeed-hildon. Fictional demo feeds in a scratch directory, no network.
RUN_SCRIPT=/project/apps/sfeed-hildon/sfeed-hildon
export SFEEDHILDON_DIR=/tmp/sfeed-hildon-demo SFEEDHILDON_BIN=/nonexistent
# screenshots of the other windows: put "Example Tech News" or "Example Tech News:0" (feed:item number) into build/sfeed-open
[ -f /project/build/sfeed-open ] && export SFEEDHILDON_OPEN="$(cat /project/build/sfeed-open)"
python3 /project/apps/sfeed-hildon/tests/make_demo.py "$SFEEDHILDON_DIR"
