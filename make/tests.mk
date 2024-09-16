TESTS_SRCS = $(wildcard $(TESTS)/*.c)
TESTS_OBJ = $(BUILD)/tests
TESTS_OBJS = $(patsubst $(TESTS)/%.c, $(TESTS_OBJ)/%, $(TESTS_SRCS))

TESTS_LDFLAGS = $(LDFLAGS) -L$(BUILD)/ -lffl 

$(TESTS_OBJ):
	@mkdir -p $@
$(TESTS_OBJS): $(TESTS_SRCS)
	@echo "[TESTS] $@"
	@$(CC) $(CFLAGS) $(TESTS_LDFLAGS) $< -o $@
	@LD_LIBRARY_PATH=$(BUILD) $@ || { echo "$@ failed."; exit 1; }

test: compile | $(TESTS_OBJ) $(TESTS_OBJS)
