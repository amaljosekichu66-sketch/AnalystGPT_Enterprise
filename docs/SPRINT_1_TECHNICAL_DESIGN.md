# Sprint 1 – Technical Design

## Architecture

main.py
    │
    ▼
UploadManager
    │
    ├── CSVReader
    ├── ExcelReader
    └── JSONReader
            │
            ▼
    pandas.DataFrame

---

## Design Principles

- Single Responsibility Principle
- Separation of Concerns
- Low Coupling
- High Cohesion
- Open for Extension, Closed for Modification

---

## Responsibilities

### UploadManager

Responsible for:

- Accepting file paths
- Detecting file extensions
- Selecting the correct reader
- Returning a DataFrame
- Logging upload operations
- Raising enterprise exceptions

Not responsible for:

- Reading CSV files
- Reading Excel files
- Reading JSON files
- Data cleaning
- Data validation

---

### CSVReader

Responsible only for reading CSV files.

Input:
- File path

Output:
- Pandas DataFrame

---

### ExcelReader

Responsible only for reading Excel files.

Input:
- File path

Output:
- Pandas DataFrame

---

### JSONReader

Responsible only for reading JSON files.

Input:
- File path

Output:
- Pandas DataFrame

---

## Module Contract

UploadManager

upload(file_path: str) -> pandas.DataFrame

CSVReader

read(file_path: str) -> pandas.DataFrame

ExcelReader

read(file_path: str) -> pandas.DataFrame

JSONReader

read(file_path: str) -> pandas.DataFrame

---

## Dependency Flow

main.py

↓

UploadManager

↓

CSVReader / ExcelReader / JSONReader

↓

Pandas DataFrame

↓

Cleaning Module