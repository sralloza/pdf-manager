import os
import re
from pathlib import Path
from typing import List

import pandas as pd

from pdf_manager.core.core import PDF

_PaL = List[Path]
_PdL = List[PDF]

__all__ = ['get_pdfs', 'get_file_list', 'make_names_relative', 'safe_delete']


def get_pdfs(path: str = './', exclude=None) -> _PdL:
    """Returns a list of PDF instances of the pdfs found in the path folder and subfolders.

    Args:
        path (str): path to scan
        exclude (str): basic pattern to exclude filenames.

    Returns:
        List[PDF]: list of PDF instances.

    """
    filenames = get_file_list(path=path, exclude=exclude)
    filenames = [x for x in filenames if 'compact_pdf.pdf' not in x.as_posix()]
    pdfs = [PDF(f) for f in filenames]
    return pdfs


def get_file_list(path: str = './', exclude=None) -> _PaL:
    """Given a directory path, it will scan and will return a list of all the filenames with its
    path.

    Args:
        path (str): path to scan.
        exclude (str): regex pattern to exclude filenames.

    Returns:
        list of all the paths.
    """

    current_path = Path(path).absolute()
    if not exclude:
        return list(current_path.rglob('*.pdf'))

    pattern = re.compile(exclude)

    result = []
    for path in current_path.rglob('*.pdf'):
        if pattern.search(path.as_posix()) is None:
            result.append(path)

    return result


def make_names_relative(df: pd.DataFrame, root: Path):
    """Makes the paths relative.

    >> make_names_relative(['/home/test/foo/bar.pdf', '/home/test/pdf.pdf'], '*home/test'):
    ['foo/bar.pdf', 'pdf.pdf'].

    Args:
        df (pd.DataFrame): dataframe to change the index from.
        root (pathlib.Path): root path.

    """
    index = [x for x in df.axes[0]]

    if len(index) == 1:
        df.index = df.index.map(os.path.basename)
        df.index = df.index.map(lambda x: '/' + x)
        return

    def algorithm(path: Path):
        return path.relative_to(root)

    df.index = df.index.map(algorithm)


def safe_delete(filename: str):
    """Deletes a file. If it exists, prints an alert. If it doesn't, it doesn't do anything.

    Args:
        filename (str): File path to delete.
    """
    try:
        os.remove(filename)
        print(f'Removed old {filename!r}')
    except FileNotFoundError:
        pass
