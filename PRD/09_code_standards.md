# Code Standards & Naming Conventions PRD

## Overview

This document establishes consistent naming conventions and code standards for the Any Agent framework to improve maintainability, readability, and developer experience.

## Status: ✅ Implementation Required

Based on QA analysis showing inconsistent naming patterns affecting code navigation and maintenance.

## Naming Convention Standards

### 1. Functions and Methods

#### ✅ Preferred Patterns
- **Descriptive verb_noun**: `extract_metadata()`, `validate_agent()`, `detect_framework()`
- **Clear purpose**: `build_docker_image()`, `start_health_monitor()`, `parse_agent_config()`
- **Consistent verb usage**:
  - `extract_*` for data extraction
  - `validate_*` for validation operations
  - `detect_*` for detection logic
  - `create_*` for object creation
  - `build_*` for construction operations

#### ❌ Avoid Generic Names
- `test()` → `test_agent_functionality()`
- `call()` → `call_agent_endpoint()`
- `validate()` → `validate_agent_structure()`
- `process()` → `process_framework_detection()`

### 2. Variables and Parameters

#### ✅ Descriptive Names
- Use full words: `description_patterns` not `desc_patterns`
- Meaningful context: `agent_metadata` not `metadata`
- Clear scope: `framework_detection_result` not `result`

#### ✅ Exception Handling
- Descriptive variables: `connection_error`, `parse_error`, `validation_error`
- Avoid single letters: `e` → `framework_error`

### 3. Classes and Types

#### ✅ Consistent Patterns
- **Singular nouns**: `ValidationResult` not `ValidationResults`
- **Clear purpose**: `FrameworkDetector` not `Detector`
- **Consistent suffixes**:
  - `*Adapter` for framework adapters
  - `*Generator` for code generators
  - `*Manager` for lifecycle managers
  - `*Client` for API clients

### 4. Private Methods

#### ✅ Clear Purpose Naming
- `_combine_python_files()` not `_aggregate_file_contents()`
- `_extract_import_patterns()` not `_get_imports()`
- `_validate_framework_structure()` not `_check_structure()`

## Implementation Priority

### High Priority - Generic CLI Functions
**File**: `src/any_agent/validation/cli.py`

Current issues:
```python
def test()      # → def test_agent_endpoints()
def call()      # → def call_a2a_endpoint()
def validate()  # → def validate_agent_deployment()
```

### Medium Priority - Context Wrapper Functions
**File**: `src/any_agent/core/context_aware_wrapper.py`

Review for consistency:
```python
create_context_aware_strands_agent()  # Good pattern
detect_agent_type()                   # Good pattern
```

### Lower Priority - Variable Naming
Review throughout codebase for:
- Single letter exception variables
- Abbreviated variable names
- Unclear parameter names

## Quality Gates

### Pre-commit Checks
- Function names must be descriptive (not generic)
- No single-letter exception variables
- Class names follow consistent patterns

### Code Review Standards
- All new functions must follow verb_noun pattern
- Generic names require justification in PR comments
- Exception handling uses descriptive variable names

## Migration Strategy

1. **Update CLAUDE.md** with naming standards ✅
2. **Create this PRD** for comprehensive guidelines ✅
3. **Fix high-priority generic CLI functions**
4. **Address medium-priority inconsistencies**
5. **Gradual improvement** of existing codebase

## Benefits

- **Improved Navigation**: Clear function names aid IDE search and code exploration
- **Reduced Cognitive Load**: Descriptive names eliminate guesswork
- **Better Maintainability**: Consistent patterns reduce learning curve for new developers
- **Enhanced Debugging**: Clear variable names improve error tracking and resolution

## Enforcement

- **Automated**: Ruff/mypy integration for basic pattern checking
- **Manual**: Code review checklist for naming convention compliance
- **Documentation**: This PRD serves as reference for all naming decisions