import os


def get_files_and_dirs(directory):
    """Return a list of files and directories in the given directory."""
    entries = os.listdir(directory)
    files = [entry for entry in entries if os.path.isfile(os.path.join(directory, entry))]
    dirs = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]
    return files, dirs
