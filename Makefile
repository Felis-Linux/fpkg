CC ?= cc
LD ?= cc

CFLAGS += -std=c99 -Wall -Wextra -I./include
LDFLAGS +=

SRC = src
INCLUDE = include
TESTS = tests
DOCS = documents

BUILD ?= build

DESTDIR ?=
SYSTEM_PREFIX ?= $(DESTDIR)/usr/local
SYSTEM_INCLUDE ?= $(SYSTEM_PREFIX)/include
SYSTEM_BIN ?= $(SYSTEM_PREFIX)/bin
SYSTEM_LIB ?= $(SYSTEM_PREFIX)/lib
all: mkbuild compile docs
mkbuild:
	@mkdir -p $(BUILD)

clean:
	@echo "[CLEAN]"
	@rm -rf $(BUILD)
	@rm -rf $(DOCS)

include make/libfl.mk
include make/tests.mk

compile: libfl_compile
install: libfl_install
$(DOCS): 
	@doxygen
docs: $(DOCS)

.PHONY: mkbuild libfl_compile libfl_install all clean test docs
