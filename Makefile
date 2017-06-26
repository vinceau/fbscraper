PY_SOURCES = fbscrape/*.py gui/*.py main.py
KV_SOURCES = gui/*.kv
ADMIN = README.md requirements.txt setup.sh

VERSION = 1.6
TARGET = fbscraper.$(VERSION).zip
OBJECTS = $(PY_SOURCES:.py=.pyc)

all:
	zip -FS $(TARGET) $(PY_SOURCES) $(KV_SOURCES) $(ADMIN)

clean:
	$(RM) $(OBJECTS) $(TARGET)
