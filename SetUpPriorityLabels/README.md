# FieldWorks Crowdin

Python utilities for interacting with the Crowdin API and parsing PO translation files.

## Project Structure

- **`crowdin_utils.py`**: Core Crowdin API utilities (projects, files, labels, strings)
- **`test_crowdin_api.py`**: CLI script for printing projects and labels
- **`beth_po_extractor.py`**: PO file parser for extracting strings, file paths, and priorities

## Requirements

- Python 3.8+
- See `requirements.txt` for dependencies

## Setup

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Updating Dependencies

To update `requirements.txt` from `requirements.in`:

```bash
pip install pip-tools
pip-compile requirements.in
```

## Configuration

Set your Crowdin API token in your system keyring:

```bash
keyring set crowdin <token_name>
```

where <token_name> could be `read_all` or `write_projects`.

## Usage

### Print Projects and Labels

For a list of Crowding API tests to run, execute

```bash
python test_crowdin_api.py
```

### Parse PO Files

```bash
python beth_po_extractor.py
```

Parses a hard-coded `.po_` file and displays:

- Total number of entries
- String count grouped by priority level
- (Optional) Distinct file paths by priority
- (Optional) matching against Crowdin strings with or without file path verification

## Crowdin API Functions

### `crowdin_utils.py`

- **`get_projects()`**: Return all projects sorted alphabetically by name
- **`select_project(project_name)`**: Select a project by name or prompt user with enumerated list
- **`select_and_fetch_files()`**: Prompt user to select a project and display file count and names
- **`export_files_to_csv()`**: Export all source files from a project to CSV
- **`get_file_path(project_id, file_id)`**: Fetch file path with folder structure (cached or API)
- **`get_project_labels(project_id)`**: Fetch all labels in a project
- **`fetch_matching_strings(search_string, options)`**: Fetch all strings matching search criteria with optional filters:
  - `project_id`: Crowdin project ID
  - `exact_match`: Match entire string only (default: False)
  - `case_sensitive`: Case-sensitive search (default: False)
  - `include_duplicates`: Include duplicate strings (default: False)
- **`add_priority_to_string(search_string, priority, project_id)`**: Assign priority label to all matching strings

## PO File Parser

### `beth_po_extractor.py`

Parses `.po_` files and extracts:

- **Paths**: File locations (starting with `/`, stripped of `::` identifiers)
- **Strings**: Translation source text (msgid field)
- **Priority**: Numeric priority from msgstr prefix (e.g., `^1^`, `^4^`) or None if not specified

### Functions

- **`parse_po_file(file_path)`**: Parse a PO file and return dict of POEntry objects keyed by lowercase string
- **`summarize_po_entries(entries, match_files, match_strings)`**: Print summary of entries grouped by priority and file paths, with optional Crowdin matching
- **`get_matching_strings(entry, match_files)`**: Search Crowdin API for a string and optionally filter by matching file paths
