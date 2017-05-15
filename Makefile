PY_SOURCES = fbscrape/*.py gui/*.py main.py
KV_SOURCES = *.kv
ADMIN = README.md requirements.txt setup.sh

VERSION = 1.4
TARGET = fbscraper.$(VERSION).zip
OBJECTS = $(PY_SOURCES:.py=.pyc)

all:
	zip -FS $(TARGET) $(PY_SOURCES) $(KV_SOURCES) $(ADMIN)

clean:
	$(RM) $(OBJECTS) $(TARGET)
