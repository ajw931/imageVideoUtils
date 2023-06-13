import re

def convert_Windows_to_WSL_path(path: str) -> str:
    """
    Converts a Windows file path to a corresponding WSL path.
    Works for Windows paths with double backslash or single forward slash.
    Doesn't always work for Windows paths with single backslash.

    Args:
        path (str): The Windows file path to convert.

    Returns:
        str: The corresponding WSL path.
    """
    # Replace backslashes with forward slashes
    path = path.replace('\\', '/')

    # Extract drive letter
    drive = re.match(r'^([A-Za-z]):/', path)
    if drive:
        drive = drive.group(1).lower()
        path = path[2:]
    else:
        drive = ''

    # Prepend "/mnt/" to drive letter
    if drive:
        drive = f'/mnt/{drive}'

    # Replace remaining slashes with colons
    #path = path.replace('/', ':')

    return f'{drive}{path}'