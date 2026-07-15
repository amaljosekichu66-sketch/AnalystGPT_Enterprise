# Sprint 2 Release Report

## Version
v2.0.0

## Sprint
Sprint 2 – Cleaning Module

## Status
✅ Completed

---

# Objective

Implement a modular data cleaning pipeline capable of preparing uploaded datasets for downstream quality checks and analytics.

---

# Features Delivered

## CleaningManager
- Coordinates the complete cleaning workflow
- Executes each cleaner in the correct order
- Resets DataFrame index after cleaning

## ColumnCleaner
- Standardizes column names
- Removes leading/trailing spaces
- Converts names to lowercase
- Replaces spaces with underscores

## TextCleaner
- Standardizes text values
- Removes extra whitespace
- Converts text to Title Case

## MissingValueCleaner
- Removes rows containing missing values
- Reports number of rows removed

## DuplicateCleaner
- Removes duplicate records
- Reports duplicate removal statistics

## DataTypeCleaner
- Converts columns to configured data types
- Supports integer, float, string, and datetime conversions

---

# Logging

Implemented centralized logging across the cleaning pipeline.

---

# Testing

Implemented automated pytest unit tests.

Results:

- ColumnCleaner ✅
- TextCleaner ✅
- MissingValueCleaner ✅
- DuplicateCleaner ✅
- DataTypeCleaner ✅

Total:
- 5 tests
- 5 passed

---

# Architecture

Pipeline:

UploadManager
↓

CleaningManager
├── ColumnCleaner
├── TextCleaner
├── MissingValueCleaner
├── DuplicateCleaner
└── DataTypeCleaner

↓

Clean DataFrame

---

# Repository

- Git tag created: v2.0.0
- Sprint completed on feature branch
- Branch pushed to GitHub

---

# Outcome

Sprint 2 successfully delivers a modular, testable, and extensible cleaning pipeline ready for integration with the Quality Module.

Next Sprint:

Sprint 3 – Quality Module