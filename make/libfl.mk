LIBFL_CFLAGS = $(CFLAGS) -fPIC -flto
LIBFL_LDFLAGS_SHARED = $(LDFLAGS) -shared -fPIC -flto

LIBFL_SHARED = libffl.so
LIBFL_SHARED_NAMED = libffl.so.0.1
LIBFL_STATIC = libffl.a

LIBFL_SOURCE_DIR = $(SRC)/libfl
LIBFL_SOURCES = $(wildcard $(LIBFL_SOURCE_DIR)/*.c)

LIBFL_OBJ_DIR = $(BUILD)/libfl
LIBFL_OBJS = $(patsubst $(LIBFL_SOURCE_DIR)/%.c, $(LIBFL_OBJ_DIR)/%.o, $(LIBFL_SOURCES))

LIBFL_INCLUDE = $(INCLUDE)/libfl
LIBFL_INCLUDES = $(wildcard $(LIBFL_INCLUDE)/*.h)

$(LIBFL_OBJ_DIR):
	@mkdir -p $@

$(BUILD)/$(LIBFL_STATIC): $(LIBFL_OBJS)
	@echo "[AR] $@"
	@ar rcs $@ $^

$(BUILD)/$(LIBFL_SHARED_NAMED): $(LIBFL_OBJS)
	@echo "[LD] $@"
	@$(CC) $^ -o $@ $(LIBFL_LDFLAGS_SHARED)

$(BUILD)/$(LIBFL_SHARED): $(BUILD)/$(LIBFL_SHARED_NAMED)
	@ln -sr $< $@

$(LIBFL_OBJ_DIR)/%.o: $(LIBFL_SOURCE_DIR)/%.c
	@echo "[CC] $< $@"
	@$(CC) -c $(LIBFL_CFLAGS) $< -o $@

libfl_compile: $(LIBFL_OBJ_DIR) mkbuild $(BUILD)/$(LIBFL_SHARED) $(BUILD)/$(LIBFL_STATIC)
libfl_install_lib: $(BUILD)/$(LIBFL_SHARED) $(BUILD)/$(LIBFL_STATIC)
	@install -Dm644 $^ $(SYS_LIB)/
libfl_install_h: $(LIBFL_INCLUDES)
	@install -Dm644 $^ $(SYS_INCLUDES)/

libfl_install: libfl_install_lib libfl_install_h
