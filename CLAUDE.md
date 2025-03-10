# Ansari Backend - Developer Guide

## Git Commit and PR Guidelines
- Do not include "Generated with Claude Code" or "Co-Authored-By: Claude" in commit messages
- Do not include "Generated with Claude Code" in PR descriptions or anywhere else
- Keep commit messages concise and descriptive
- Use imperative mood in commit messages (e.g., "Add feature" not "Added feature")

## Build/Test/Lint Commands
- Install dependencies: `pip install -r requirements.txt`
- Run database setup: `python setup_database.py`
- Run backend service: `uvicorn main_api:app --reload`
- Run CLI version (interactive): 
  - Claude: `python src/ansari/app/main_stdio.py -a AnsariClaude`
  - OpenAI: `python src/ansari/app/main_stdio.py -a Ansari`
- Run CLI with direct input:
  - `python src/ansari/app/main_stdio.py -i "your question here"` 
  - `python src/ansari/app/main_stdio.py --input "your question here"`
- Run tests: `pytest tests/`
- Run single test: `pytest tests/path/to/test.py::test_function_name`
- Run tests with specific marker: `pytest -m integration`
- Lint code: `ruff check src/`
- Format code: `ruff format src/`

## Code Style Guidelines
- **Imports**: Use absolute imports within the `ansari` package
- **Formatting**: Double quotes for strings, 4-space indentation
- **Line length**: 127 characters maximum
- **Types**: Use Python type hints for function parameters and return types
- **Naming**: Use snake_case for variables/functions, PascalCase for classes
- **Error handling**: Use try/except blocks with specific error types
- **Logging**: Use the logger from `ansari.ansari_logger.get_logger()`
- **Documentation**: Add docstrings to functions, especially complex ones
- **Testing**: Create unit tests in `tests/unit/` and integration tests in `tests/integration/`
- **Test-first development**: Always write tests before shipping features
  - Write tests that validate both expected behavior and edge cases
  - When fixing bugs, first write a test that reproduces the issue
  - Run tests frequently during development to catch regressions

## Testing Best Practices
- Run tests before committing: `pytest tests/`
- Run specific test categories: `pytest tests/unit/` or `pytest tests/integration/`
- Add tests for new functionality in the appropriate directory
- Use fixture factories to keep tests maintainable
- Test both happy path and error conditions
- Keep tests independent (no dependencies between test functions)