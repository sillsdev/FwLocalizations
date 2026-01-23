"""Utility functions for interacting with the Crowdin API."""

from crowdin_api import CrowdinClient
import keyring
import csv
import os
from typing import Any, Callable, TypedDict


class Pagination(TypedDict):
    offset: int
    limit: int


class CrowdinItem(TypedDict):
    data: dict[str, Any]


class CrowdinListResponse(TypedDict):
    data: list[CrowdinItem]
    pagination: Pagination


class SearchOptions(TypedDict, total=False):
    project_id: str
    case_sensitive: bool
    exact_match: bool
    include_duplicates: bool


fw_project_name: str = "Fieldworks"
fw_project_id: int = 379603
fw_priority_label_ids: dict[int, int] = { 1: 11, 2: 9, 3: 7, 4: 5, 5: 3 }

token: str | None = keyring.get_password('crowdin', 'write_projects') #or 'read_all' for safer testing

client: CrowdinClient = CrowdinClient(token=token)

# Cache for file paths to avoid repeated API calls
_file_path_cache: dict[tuple[int, int], str] = {}


def _load_file_path_cache_from_csv(csv_filename: str = f'{fw_project_name}_files.csv') -> None:
    """Populate the file path cache from a CSV if present."""
    if not os.path.exists(csv_filename):
        return

    with open(csv_filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                file_id = int(row.get('file_id', ''))
            except ValueError:
                continue
            file_path = row.get('file_path', '')
            _file_path_cache[(fw_project_id, file_id)] = file_path


def paginate_list(fetch_page: Callable[[int, int], CrowdinListResponse], page_limit: int = 100) -> list[dict[str, Any]]:
    """Fetch all pages from a Crowdin list endpoint.

    Args:
        fetch_page: Callable that accepts (limit, offset) and returns a Crowdin list response.
        page_limit: Page size to request from the API.

    Returns:
        Aggregated list of Crowdin items across all pages.
    """
    offset: int = 0
    items: list[dict[str, Any]] = []

    while True:
        response: CrowdinListResponse = fetch_page(page_limit, offset)
        batch: list[dict[str, Any]] = [page['data'] for page in response['data']]
        items.extend(batch)
        if len(batch) < page_limit:
            break
        offset += page_limit

    return items


def get_projects() -> list[dict[str, Any]]:
    """Return all Crowdin projects sorted alphabetically by name."""
    # https://crowdin.github.io/crowdin-api-client-python/api_resources/projects/resource.html#crowdin_api.api_resources.projects.resource.ProjectsResource.list_projects
    # https://support.crowdin.com/developer/api/v2/#operation/api.projects.getMany
    projects: CrowdinListResponse = client.projects.list_projects()
    data = [item['data'] for item in projects['data']]
    return sorted(data, key=lambda x: x['name'])


def select_project(project_name: str | None = None) -> dict[str, Any]:
    """Select and return a project.

    If project_name is specified, return the matching project if found.
    Otherwise, display an enumerated list and prompt user to select by number.

    Args:
        project_name: Optional project name to search for.

    Returns:
        The selected project dictionary.
    """
    projects: list[dict[str, Any]] = get_projects()

    if project_name:
        for project in projects:
            if project['name'] == project_name:
                return project
        print(f'Project "{project_name}" not found.')

    print(f'\n{len(projects)} projects:\n')
    for i, project in enumerate(projects, start=1):
        print(f'{i}. {project["name"]}')

    selection: str = input('\nSelect project (enter number): ')
    return projects[int(selection) - 1]


def list_files_lambda(project_id: int = fw_project_id) -> Callable[[int, int], CrowdinListResponse]:
    """Return a lambda function to list files for a given project ID."""
    # https://crowdin.github.io/crowdin-api-client-python/api_resources/source_files/resource.html#crowdin_api.api_resources.source_files.resource.SourceFilesResource.list_files
    # https://support.crowdin.com/developer/api/v2/#operation/api.projects.files.getMany
    return lambda limit, offset: client.source_files.list_files(project_id, limit=limit, offset=offset)


def select_and_fetch_files() -> None:
    """Prompt user to select a project, then fetch and display source file information.

    Presents enumerated list of projects (starting at 1), prompts for numeric selection,
    fetches all source files using paginated API calls (100 per page), and prints the
    total count and first ten file names (with ellipsis if more exist).
    """
    selected_project: dict[str, Any] = select_project()

    source_files: list[dict[str, Any]] = paginate_list(list_files_lambda(selected_project['id']))
    
    print(f'\n{selected_project["name"]} has {len(source_files)} source file(s):')
    for file in source_files[:10]:
        print(file['name'])
    if len(source_files) > 10:
        print('...')


def export_files_to_csv() -> None:
    """Export project files to CSV with file_id and file_path columns.

    Prompts to select a project, fetches all source files, and saves them
    to a CSV file named '<project_name>_files.csv'.
    """
    selected_project: dict[str, Any] = select_project()
    
    source_files: list[dict[str, Any]] = paginate_list(list_files_lambda(selected_project['id']))
    
    csv_filename: str = f"{selected_project['name']}_files.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['file_id', 'file_path'])
        
        for file in source_files:
            file_id: int = file.get('id', '')
            file_path: str = file.get('path', file.get('name', ''))
            writer.writerow([file_id, file_path])
    
    print(f'\nExported {len(source_files)} files to {csv_filename}')


def get_file_path(project_id: int, file_id: Any) -> str:
    """Fetch the file path for a given file ID from a project.

    Checks local cache first, then queries the Crowdin API if not found.

    Args:
        project_id: The Crowdin project ID.
        file_id: The Crowdin file ID (int or convertible to int).

    Returns:
        The file path with folder structure, or 'Unknown' if not found.
    """
    if not _file_path_cache and project_id == fw_project_id:
        _load_file_path_cache_from_csv()

    file_id_int: int = int(file_id)
    project_id_int: int = int(project_id)
    
    cache_key: tuple[int, int] = (project_id_int, file_id_int)
    
    # Check cache first
    if cache_key in _file_path_cache:
        return _file_path_cache[cache_key]
    
    #return KeyError('File ID not found in cache, would have to fetch from API.')
    
    # https://crowdin.github.io/crowdin-api-client-python/api_resources/source_files/resource.html#crowdin_api.api_resources.source_files.resource.SourceFilesResource.get_file
    # https://support.crowdin.com/developer/api/v2/#tag/Source-Files/operation/api.projects.files.get
    file_response: dict[str, Any] = client.source_files.get_file(file_id_int, project_id_int)
    file_data: dict[str, Any] = file_response.get('data', {})
    path: str = file_data.get('path', file_data.get('name', 'Unknown'))
    
    # Cache the result
    _file_path_cache[cache_key] = path
    return path


def list_labels_lambda(project_id: int = fw_project_id) -> Callable[[int, int], CrowdinListResponse]:
    """Return a lambda function to list labels for a given project ID."""
    # https://crowdin.github.io/crowdin-api-client-python/api_resources/labels/resource.html#crowdin_api.api_resources.labels.resource.LabelsResource.list_labels
    # https://support.crowdin.com/developer/api/v2/#operation/api.projects.labels.getMany
    return lambda limit, offset: client.labels.list_labels(project_id, limit=limit, offset=offset)


def get_project_labels(project_id: int) -> list[dict[str, Any]]:
    """Fetch all labels for a given project.

    Paginates through all labels using the Crowdin API, loading all pages
    (100 items per page).

    Args:
        project_id: The Crowdin project ID.

    Returns:
        List of all label dictionaries for the project.
    """
    return paginate_list(list_labels_lambda(project_id))


def list_strings_lambda(filter:str, project_id: int = fw_project_id) -> Callable[[int, int], CrowdinListResponse]:
    """Return a lambda function for paginated string list queries with text scope filter."""
    # https://crowdin.github.io/crowdin-api-client-python/api_resources/source_strings/resource.html#crowdin_api.api_resources.source_strings.resource.SourceStringsResource.list_strings
    # https://support.crowdin.com/developer/api/v2/#operation/api.projects.strings.getMany
    return lambda limit, offset: client.source_strings.list_strings(
        project_id,
        filter=filter,
        limit=limit,
        offset=offset,
        scope="text",
    )


def fetch_matching_strings(search_string: str, options: SearchOptions | None = None) -> list[dict[str, Any]]:
    """Fetch all strings matching the given search string from a project.

    Selects a project (by name if provided in options, otherwise via user selection) and
    retrieves all strings matching the search term (by identifier, text, or context),
    paginating through all results (100 per page). Optionally filters by case sensitivity
    and exact match.

    Args:
        search_string: The string to search for (filters by identifier, text, or context).
        options: Optional search options dict with keys:
            - project_name: Project name to search in. If not provided, user will be prompted.
            - case_sensitive: Whether search is case-sensitive (default: False).
            - exact_match: Whether to match entire string only (default: False).
            - include_duplicates: Whether to include strings marked as duplicates (default: False).

    Returns:
        A list of all matching string dictionaries.
    """
    if options is None:
        options = {}

    case_sensitive: bool = options.get('case_sensitive', False)
    exact_match: bool = options.get('exact_match', False)
    include_duplicates: bool = options.get('include_duplicates', False)

    project_id: int | None = options.get('project_id')
    if project_id is None:
        selected_project: dict[str, Any] = select_project(project_id)
        project_id: int = selected_project['id']

    matching_strings: list[dict[str, Any]] = []

    strings_pages: list[dict[str, Any]] = paginate_list(list_strings_lambda(search_string, project_id))

    # If no match and search string contains < or >, search again with HTML entities
    if not strings_pages and ('<' in search_string or '>' in search_string):
        search_string = search_string.replace('<', '&lt;').replace('>', '&gt;')
        strings_pages = paginate_list(list_strings_lambda(search_string, project_id))

    for item in strings_pages:
        text: str = item.get('text', '')
        is_duplicate: bool = item.get('isDuplicate', False)

        if is_duplicate and not include_duplicates:
            continue

        search_text: str = search_string if case_sensitive else search_string.lower()
        compare_text: str = text if case_sensitive else text.lower()

        if exact_match:
            if search_text == compare_text:
                matching_strings.append(item)
        else:
            if search_text in compare_text:
                matching_strings.append(item)

    return matching_strings


def add_priority_to_string(search_string: str = '', priority: int | None = None, project_id: int | None = fw_project_id) -> int | None:
    """Assign a priority label to all strings matching the search criteria.

    Searches the project for exact matches of the search string and applies a priority
    label (1-5). Prompts for search_string and priority if not provided. Returns the
    number of strings updated, or None if no matches found.

    Uses `fw_priority_label_ids` mapping to resolve Crowdin label IDs.

    Args:
        search_string: String to search for. If empty, user is prompted.
        priority: Desired priority (1-5). If invalid/None, user is prompted.
        project_id: Crowdin project ID (default: fw_project_id).

    Returns:
        Number of strings successfully labeled, or None if no matches found.
    """
    if not search_string:
        search_string = input('\nEnter search string: ')

    print(f'Labeling strings matching: {search_string.replace("\n", "\\n")}')

    matching_strings = fetch_matching_strings(
        search_string,
        {'project_id': project_id, 'exact_match': True}
    )

    if not matching_strings:
        print('\tNo matching strings found.')
        return None

    # Prompt until a valid priority (1-5) is provided
    while priority is None or priority not in fw_priority_label_ids:
        try:
            entered = input('Enter priority (1-5): ')
            priority = int(entered)
        except ValueError:
            print('Invalid number. Please enter 1-5.')
            continue
        if priority not in fw_priority_label_ids:
            print('Priority must be 1-5.')

    label_id = fw_priority_label_ids[priority]

    updated_count = 0
    already_labeled_count = 0
    operations: list[dict[str, Any]] = []

    for item in matching_strings:
        string_id = item.get('id')
        if string_id is None:
            continue

        current_labels: list[int] = item.get('labelIds') or []
        if label_id in current_labels:
            already_labeled_count += 1
            continue

        new_labels = current_labels + [label_id]
        operations.append({'op': 'replace', 'path': f'/{string_id}/labelIds', 'value': new_labels})

    if operations:
        try:
            # https://support.crowdin.com/developer/api/v2/#tag/Source-Strings/operation/api.projects.strings.batchPatch
            client.source_strings.string_batch_operation(projectId=fw_project_id, data=operations)
            updated_count = len(operations)
        except Exception as e:
            print(f'Failed to batch update strings: {e}')

    print(f'\tAdded priority {priority} to {updated_count} of {len(matching_strings)} matching strings.')
    if already_labeled_count:
        print(f'\t\t{already_labeled_count} strings were already labeled.')
    
    return updated_count
