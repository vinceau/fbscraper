PY_SOURCES = fbscrape/*.py main.py kivyview.py searchview.py
KV_SOURCES = *.kv
ADMIN = README.md requirements.txt setup.sh

TARGET = fbscraper.zip 
OBJECTS = $(PY_SOURCES:.py=.pyc)

all:
	zip -FS $(TARGET) $(PY_SOURCES) $(KV_SOURCES) $(ADMIN)

clean:
	$(RM) $(OBJECTS) $(TARGET)
