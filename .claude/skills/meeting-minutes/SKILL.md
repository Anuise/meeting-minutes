```markdown
# meeting-minutes Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development conventions and workflows used in the `meeting-minutes` Python repository. It covers file naming, import/export patterns, commit message styles, and testing approaches. By following these patterns, contributors can maintain consistency and quality across the codebase.

## Coding Conventions

### File Naming
- Use **camelCase** for Python file names.
  - Example: `meetingNotes.py`, `actionItems.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import formatMinutes
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['formatMinutes', 'parseAgenda']
    ```

### Commit Messages
- Use **Conventional Commits** with the `feat` prefix for new features.
  - Example:
    ```
    feat: add support for exporting minutes to PDF
    ```

## Workflows

### Adding a New Feature
**Trigger:** When implementing a new feature or enhancement  
**Command:** `/add-feature`

1. Create a new branch for your feature.
2. Name new files using camelCase.
3. Use relative imports for internal modules.
4. Add named exports in your module.
5. Write or update tests in files matching `*.test.*`.
6. Commit using the conventional commit format with `feat` prefix.
7. Open a pull request for review.

### Running Tests
**Trigger:** When validating code changes  
**Command:** `/run-tests`

1. Identify test files (pattern: `*.test.*`).
2. Run tests using the preferred Python test runner (e.g., `pytest` or `unittest`).
   - Example:
     ```bash
     python -m unittest discover
     ```
3. Ensure all tests pass before merging changes.

## Testing Patterns

- Test files follow the pattern: `*.test.*` (e.g., `meetingNotes.test.py`).
- The specific testing framework is not enforced, but standard Python test runners like `unittest` or `pytest` are recommended.
- Place tests alongside or near the modules they test.
- Example test file structure:
  ```python
  # meetingNotes.test.py
  import unittest
  from .meetingNotes import formatMinutes

  class TestFormatMinutes(unittest.TestCase):
      def test_basic_format(self):
          self.assertEqual(formatMinutes(...), ...)
  ```

## Commands
| Command        | Purpose                                   |
|----------------|-------------------------------------------|
| /add-feature   | Start the workflow for adding a new feature|
| /run-tests     | Run all test files in the repository      |
```