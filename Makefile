.PHONY: lint format test
TARGET ?= nk_autocode samples
MYPY_TARGET ?= nk_autocode
lint:
	ruff check $(TARGET)
	mypy $(MYPY_TARGET)
format:
	ruff format $(TARGET)
	ruff check --fix $(TARGET)
test:
	pytest
