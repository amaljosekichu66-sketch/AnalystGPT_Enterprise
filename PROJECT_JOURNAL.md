# Project Journal

## Sprint 0

### Date
03 July 2026

### Completed

- Created project
- Installed VS Code
- Installed Python Extension
- Verified Python 3.10.5
- Selected Interpreter
- Created README
- Created src folder
- Created project modules
- Created main.py
- Executed first Python program

### Lessons Learned

- Business before code
- Architecture before implementation
- main.py is an orchestrator
- src contains application code
- Upload Module should return a DataFrame
- Separation of Concerns
- Modular Design

# Project Journal

## Sprint 0

### Date
03 July 2026

### Completed

- Created project
- Installed VS Code
- Installed Python Extension
- Verified Python 3.10.5
- Selected Interpreter
- Created README
- Created src folder
- Created project modules
- Created main.py
- Executed first Python program

### Lessons Learned

- Business before code
- Architecture before implementation
- main.py is an orchestrator
- src contains application code
- Upload Module should return a DataFrame
- Separation of Concerns
- Modular Design

---

## Sprint 0.5

### Date
### 04 July 2026

### Completed

- Created `core` package
- Added `constants.py`
- Added `config.py`
- Added `logger.py`
- Added `exceptions.py`
- Added `__init__.py` files to all packages
- Implemented basic logging infrastructure
- Implemented application configuration
- Implemented application constants
- Created first custom exception
- Performed first smoke test
- Reviewed application architecture
- Defined module responsibilities
- Defined dependency direction
- Established shared infrastructure design

### Lessons Learned

- Shared infrastructure belongs inside `core`
- Business modules should depend on `core`
- `core` must never depend on business modules
- Stable contracts reduce coupling
- Upload should always return a Pandas DataFrame
- Configuration and constants serve different purposes
- Logger and log are different concepts
- Handlers decide where logs are written
- Custom exceptions improve maintainability
- Good architecture reduces cognitive load
- Design before implementation