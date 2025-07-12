.PHONY: lint format test
TARGET ?= nk_autocode nk_autodoc samples
MYPY_TARGET ?= nk_autocode nk_autodoc
lint:
	ruff check $(TARGET)
	mypy $(MYPY_TARGET)
format:
	ruff format $(TARGET)
	ruff check --fix $(TARGET)
test:
	pytest
