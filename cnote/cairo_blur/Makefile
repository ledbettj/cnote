TARGET = cairo_blur.so
SOURCE = cairo_blur.c
TOOL   = ./setup.py

.PHONY: clean

$(TARGET): $(SOURCE) $(TOOL)
	$(TOOL) build_ext -i

clean:
	rm -f $(TARGET)
	rm -rf build
