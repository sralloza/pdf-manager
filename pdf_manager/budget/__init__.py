from pathlib import Path
from typing import Union, Tuple, List

import pandas as pd
from colorama import Fore, Style

from pdf_manager.core.core import PdfTypes, PDF
from pdf_manager.core.utils import get_pdfs, make_names_relative

_SP = Union[str, Path]
_PdL = List[PDF]
_C = Tuple[pd.DataFrame, _PdL]

__all__ = ['create_budget']

def _create_budget(path: _SP = './', price_per_sheet: float = 0.03, exclude=None) -> _C:
    """It scans recursively the path given searching pdf files, and will calculate the printing
    price of each of the pdf files found by multiplying price_per_sheet with the number of pages
    detected in the pdf. It will sum up all the data and will return it as a pd.DataFrame.

    Args:
        path (str): path to scan.
        price_per_sheet (float): price per sheet.
        exclude (str): basic pattern to exclude filenames.

    Returns:
        pd.DataFrame: dataframe with the filepath as index, and the number of pages and the price
            as columns. The last row is the 'total' row.

    """
    path = Path(path).absolute()
    pdfs = get_pdfs(path=path, exclude=exclude)
    df = pd.DataFrame(columns=['filepath', 'pages', 'price'])
    df.set_index(['filepath'], inplace=True)

    errors = []

    for pdf in pdfs:
        if pdf.get_type() != PdfTypes.A4:
            errors.append(pdf)
            continue

        df.loc[pdf.filepath] = (pdf.pages, pdf.pages * price_per_sheet)

    make_names_relative(df, path)

    df.sort_values(['pages'], inplace=True, ascending=False)
    df.loc['Total'] = df.loc[:, 'pages'].sum(), df.loc[:, 'price'].sum()
    df.loc[:, 'pages'] = df.loc[:, 'pages'].astype(int)

    return df, errors


def create_budget(path: _SP = './', price_per_sheet=0.03, exclude: str = None):
    """Interface for create_budget(). First will search and concat the pdf files found. Then, it
    will print the errors and the success. Finally, the budget will be printed.

    Args:
        path (str or Path): path to scan.
        price_per_sheet (float): price per sheet.
        exclude (str): regex pattern to exclude filenames.

    """
    df, errors = _create_budget(path=path, price_per_sheet=price_per_sheet, exclude=exclude)

    for pdf in errors:
        print(Fore.RED + f'TypeError: {pdf.get_type()!r} -- {pdf.filepath!r}')

    print(Style.RESET_ALL, end='')
    print()
    print(df)
