.PHONY: lint format test
TARGET ?= nk_autocode
lint:
	ruff check $(TARGET)
	mypy $(TARGET)
format:
	ruff format $(TARGET)
	ruff check --fix $(TARGET)
test:
	pytest
