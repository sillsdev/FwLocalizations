from crowdin_utils import (
    add_priority_to_string,
    export_files_to_csv,
    get_projects,
    select_project,
    select_and_fetch_files,
    get_file_path,
    get_project_labels,
    fetch_matching_strings,
    fw_project_id,
    fw_project_name,
)


def print_projects() -> None:
    """Display all projects (sorted by name) with their IDs."""
    data = get_projects()
    print(f'{len(data)} projects:')
    for project in data:
        print(project['id'], project['name'])


def print_project_labels(project_name: str | None = None) -> None:
    """Print all labels for the selected project.

    If `project_name` is provided, selects that project by name; otherwise,
    prompts the user to choose from an enumerated list. Prints the total
    labels and enumerates their titles.
    """
    selected_project = select_project(project_name)
    labels = get_project_labels(selected_project['id'])

    print(f"\nProject {selected_project['name']} has {len(labels)} label(s):")
    for label in labels:
        print(f"{label.get('id', 'Unknown')}: {label.get('title', 'Unknown')}")


def search_matching_strings(search_string: str = '') -> None:
    if not search_string:
        search_string = input('\nEnter search string: ')
    matching_strings = fetch_matching_strings(
        search_string,
        {'project_id': fw_project_id, 'exact_match': True}
    )

    print(f'\nFound {len(matching_strings)} matching string(s):')
    for string in matching_strings[:10]:
        text: str = string.get('text', 'N/A')
        file_id: str = string.get('fileId', 'N/A')
        file_path: str = get_file_path(fw_project_id, file_id) if file_id != 'N/A' else 'N/A'
        print(f'[{file_path}] {text}')
    if len(matching_strings) > 10:
        print('...')


if __name__ == '__main__':
    print('\nAvailable tests:\n')
    print('1. print_projects() - Display all projects with IDs')
    print('2. select_and_fetch_files() - Show files for selected project')
    print('3. search_matching_strings() - Search strings in Fieldworks project')
    print('4. print_project_labels() - Display labels for Fieldworks project')
    print('5. export_files_to_csv() - Export project files to CSV')
    print('6. add_priority_to_string() - Add priority label to matching strings')

    selection: str = input('\nSelect test (enter number 1-6): ')

    match selection:
        case '1':
            print_projects()
        case '2':
            select_and_fetch_files()
        case '3':
            search_matching_strings()
        case '4':
            print_project_labels(fw_project_name)
        case '5':
            export_files_to_csv()
        case '6':
            add_priority_to_string()
        case _:
            print('Invalid selection.')
