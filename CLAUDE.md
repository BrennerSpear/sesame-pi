# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run application: `python voice_interaction.py`
- Activate venv: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
- Install dependencies: `pip install -r requirements.txt`
- Lint code: `flake8 voice_interaction.py`
- Typecheck: `mypy voice_interaction.py`

## Code Style Guidelines
- **Imports**: Group imports: standard library, third-party, local modules. Sort alphabetically.
- **Formatting**: Follow PEP 8, limit lines to 100 characters.
- **Typing**: Type hints encouraged for function parameters and return values.
- **Error Handling**: Use try/except with specific error types, log errors with context.
- **Naming**: Use snake_case for functions/variables, CamelCase for classes.
- **Logging**: Use Python's logging library with appropriate log levels.
- **Platform Compatibility**: Use platform-specific code with conditional imports.
- **Comments**: Docstrings for classes/methods using triple quotes.

## Notes
- Use additional_headers instead of extra_headers
- Don't try to run any of the python scripts - I'll do that separately