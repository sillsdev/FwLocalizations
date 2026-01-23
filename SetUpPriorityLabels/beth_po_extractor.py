"""Parser for Beth's PO file format to extract strings, file paths, and priorities."""

from dataclasses import dataclass, field
from typing import Any, Optional
import re

from crowdin_utils import add_priority_to_string, fetch_matching_strings, fw_project_id, get_file_path

@dataclass
class POEntry:
    """Represents a single entry from a PO file."""
    paths: list[str] = field(default_factory=list)
    string: str = ""
    priority: Optional[int] = None

    def __repr__(self) -> str:
        paths_str = ", ".join(self.paths) if self.paths else "No paths"
        return (
            f"POEntry(paths=[{paths_str}], "
            f"string={repr(self.string[:50])}, priority={self.priority})"
        )


@dataclass
class MatchingStringsResult:
    """Structured result for matching strings lookup."""

    string_matches: list[dict[str, Any]]
    string_ids_with_file_matches: list[str]


def parse_po_file(file_path: str) -> dict[str, POEntry]:
    """Parse a PO file and extract entries with paths, strings, and priorities.

    Reads a `.po_` file and extracts file paths from comment lines (starting with /),
    strings from msgid fields, and priorities from msgstr fields (e.g., ^1^).
    Entries are deduplicated by lowercase string, keeping the highest priority.

    Args:
        file_path: Path to the .po_ file to parse.

    Returns:
        Dictionary of POEntry objects keyed by lowercase string, with merged entries
        and deduplicated paths.
    """
    entries: dict[str, POEntry] = {}

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by double newlines to separate entries
    blocks = content.split('\n\n')

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        entry = POEntry()
        lines = block.split('\n')

        i = 0
        # Extract file paths from comment lines
        while i < len(lines) and lines[i].startswith('#.'):
            path_line = lines[i][3:].strip()  # Remove '#. ' prefix
            # Only include paths that start with '/' (skip descriptive comments)
            if path_line.startswith('/'):
                # Strip everything after '::' (e.g., resource identifier)
                path = path_line.split('::')[0]
                # Replace /| with the full path prefix
                if path.startswith('/|'):
                    path = path.replace('/|', '/DistFiles/Language Explorer/Configuration/', 1)
                entry.paths.append(path)
            i += 1

        # Skip other comment lines (metadata, etc.)
        while i < len(lines) and lines[i].startswith('#'):
            i += 1

        # Extract msgid (the string to translate)
        msgid_lines: list[str] = []
        if i < len(lines) and lines[i].startswith('msgid'):
            line = lines[i]
            i += 1

            # Handle empty msgid (multiline string follows)
            if line == 'msgid ""':
                # Collect subsequent quoted lines until msgstr
                while i < len(lines) and lines[i].startswith('"'):
                    # Extract content between quotes
                    content_line = lines[i][1:-1]  # Remove surrounding quotes
                    msgid_lines.append(content_line)
                    i += 1
            else:
                # Single line msgid: msgid "content"
                match = re.match(r'msgid "(.*)"', line)
                if match:
                    msgid_lines.append(match.group(1))

        # Join multiline strings
        msgid = ''.join(msgid_lines).replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '\"').replace('\\\\', '\\')
        if not msgid.strip():
            continue  # Skip entries with empty msgid
        entry.string = msgid

        # Extract priority from msgstr (e.g., "^1^" or "^4^")
        if i < len(lines) and lines[i].startswith('msgstr'):
            line = lines[i]

            if line == 'msgstr ""':
                # Multiline msgstr - check first quoted line for priority
                if i + 1 < len(lines) and lines[i + 1].startswith('"'):
                    first_line = lines[i + 1][1:-1]  # Remove surrounding quotes
                    priority_match = re.match(r'\^(\d+)\^', first_line)
                    if priority_match:
                        entry.priority = int(priority_match.group(1))
            else:
                # Single line msgstr
                match = re.match(r'msgstr "(.*)"', line)
                if match:
                    priority_match = re.match(r'\^(\d+)\^', match.group(1))
                    if priority_match:
                        entry.priority = int(priority_match.group(1))

        if entry.string or entry.paths:
            key = entry.string.lower()
            if key in entries:
                existing = entries[key]
                # Replace if new entry has higher priority (lower number)
                if entry.priority is not None and (existing.priority is None or entry.priority < existing.priority):
                    # Merge paths and update entry
                    entry.paths = list(set(existing.paths + entry.paths))
                    entries[key] = entry
                else:
                    # Keep existing, but merge paths
                    existing.paths = list(set(existing.paths + entry.paths))
            else:
                entries[key] = entry

    return entries


def summarize_po_entries(entries: list[POEntry], match_files: bool = False, match_strings: bool = False) -> None:
    """Print a summary of PO entries grouped by priority and file paths.

    Prints total entry count, strings per priority level, and optionally distinct
    file paths per priority. Can also search Crowdin for matching strings and verify
    file path matches.

    Args:
        entries: List of POEntry objects to summarize.
        match_files: If True, count distinct file paths per priority and verify matches
                     against Crowdin file paths.
        match_strings: If True, search Crowdin for matching strings and categorize as
                       no match, weak match (string found), or strong match (string and
                       file path found).
    """
    print(f'{len(entries)} entries\n')

    # Count strings and distinct paths by priority
    priority_counts: dict[Optional[int], int] = {}
    priority_paths: dict[Optional[int], set[str]] = {}
    path_priority_counts: dict[str, dict[Optional[int], int]] = {}
    match_counts: dict[Optional[int], dict[str, int]] = {}
    
    for entry in entries:
        priority = entry.priority
        priority_counts[priority] = priority_counts.get(priority, 0) + 1
        if match_files:
            if priority not in priority_paths:
                priority_paths[priority] = set()
            priority_paths[priority].update(entry.paths)

            for path in entry.paths:
                path_counts = path_priority_counts.setdefault(path, {})
                path_counts[priority] = path_counts.get(priority, 0) + 1

        if entry.priority is not None and match_strings:
            string_match_result = get_matching_strings(entry, match_files=match_files)
            if match_files:
                if priority not in match_counts:
                    match_counts[priority] = {'no_match': 0, 'weak_match': 0, 'strong_match': 0}
                if string_match_result.string_ids_with_file_matches:
                    match_counts[priority]['strong_match'] += 1
                elif string_match_result.string_matches: 
                    match_counts[priority]['weak_match'] += 1
                else:
                    print(f'No match for priority {priority} string: {entry.string}')
                    match_counts[priority]['no_match'] += 1
            else:
                if priority not in match_counts:
                    match_counts[priority] = {'no_match': 0, 'match': 0}
                if string_match_result.string_matches: 
                    match_counts[priority]['match'] += 1
                else:
                    print(f'No match for priority {priority} string: {entry.string}')
                    match_counts[priority]['no_match'] += 1

    # Print summary
    print('String counts by priority:')
    for priority in sorted(priority_counts.keys(), key=lambda x: (x is None, x)):
        count = priority_counts[priority]
        priority_label = f'Priority {priority}' if priority is not None else 'No priority'
        if match_files:
            distinct_paths = len(priority_paths[priority])
            print(f'  {priority_label}: {count} strings from {distinct_paths} distinct files')
        else:
            print(f'  {priority_label}: {count} strings')

    if match_files:
        print('\nPriority counts by path:')
        path_items = list(path_priority_counts.items())
        path_items.sort(key=lambda item: (-sum(count for p, count in item[1].items() if p is not None), item[0]))

        for path, counts in path_items[:3]:
            parts = []
            for priority, count in sorted(counts.items(), key=lambda x: (x[0] is None, x[0])):
                label = f'P{priority}' if priority is not None else 'None'
                parts.append(f'{label}:{count}')
            print(f'  {path}: ' + ', '.join(parts))

    if match_strings:
        print('\nMatch summary by priority:')
        for priority in sorted(match_counts.keys(), key=lambda x: (x is None, x)):
            counts = match_counts[priority]
            priority_label = f'Priority {priority}' if priority is not None else 'No priority'
            if match_files:
                print(f'  {priority_label}: '
                    f"{counts['no_match']} no match, "
                    f"{counts['weak_match']} weak match, "
                    f"{counts['strong_match']} strong match")
            else:
                print(f'  {priority_label}: '
                    f"{counts['no_match']} no match, "
                    f"{counts['match']} match")


def get_matching_strings(entry: POEntry, match_files: bool = False) -> MatchingStringsResult:
    """Search Crowdin for matching strings and optionally verify file path matches.

    Searches the Crowdin API for exact matches of the entry's string using exact_match
    filter. If match_files is True, verifies each match against the entry's file paths.

    Args:
        entry: POEntry object containing the string to search for and file paths.
        match_files: If True, filter results to only include strings matching entry's
                     file paths.

    Returns:
        MatchingStringsResult containing all string matches and subset with matching
        file paths.
    """
    #print(f'\nSearching for priority {entry.priority} string (from {len(entry.paths)} files):\n{entry.string}')
    string_matches = fetch_matching_strings(
        entry.string,
        {'project_id': fw_project_id, 'exact_match': True}
    )
    string_ids_with_file_matches: list[str] = []
    if match_files:
        for string in string_matches:
            file_id: str = string.get('fileId', 'N/A')
            file_path: str = get_file_path(fw_project_id, file_id) if file_id != 'N/A' else 'N/A'
            if file_path in entry.paths:
                string_ids_with_file_matches.append(string.get('id', 'N/A'))
    #print(f'Found {len(string_matches)} matching strings ({len(string_ids_with_file_matches)} with matching file)')
    return MatchingStringsResult(
        string_matches=string_matches,
        string_ids_with_file_matches=string_ids_with_file_matches,
    )


if __name__ == '__main__':
    # Example usage
    po_file = 'messages.en-ca.po_'
    entries = parse_po_file(po_file)

    entries_list = list(entries.values())
    summarize_po_entries(entries_list)

    start = next((i for i, entry in enumerate(entries_list) if entry.string.startswith('make-it-exit') ), None)

    if start is None:
        exit('Starting string not found in entries.')

    number_to_process = 0

    with open('po-no-match.txt', 'a', encoding='utf-8') as no_match_file:
        for entry in entries_list[start:start+number_to_process]:
            if entry.string == 'Choose writing system(s) of translated lists:':
                # This throws a permission-denied error when updating in Crowdin via API; added manually
                continue

            if entry.string == '&Writing System(s):':
                # This throws a permission-denied error when updating in Crowdin via API; added manually
                continue

            if entry.string == 'Word':
                # Too many non-exact matches to fetch and sort through; added manually
                continue

            if entry.priority:
                update_count = add_priority_to_string(search_string=entry.string, priority=entry.priority)
                if update_count is None:
                    no_match_file.write(f'{entry.priority}\t' + entry.string.replace('\n', '\\n').replace('\t', '\\t') + '\n')
