# sfeed-hildon: a native RSS/Atom reader (Python 3 + hildonlite) on top of sfeed. Targets and conventions: ../../mk/app.mk
override APP     := sfeed-hildon
VERSION ?= 0.1
REV     ?= 1maemo4
DEPS    := hildonlite
RUN_CMD := /usr/bin/sfeed-hildon
ICON_OUT := icons/64.png
include ../../mk/app.mk
