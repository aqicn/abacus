
all: test
	python app.py

test:
	ruff check airbacus

