"""Program designed for process pdf files and printing them."""

import argparse
import os
import sys
import warnings
from dataclasses import dataclass, field
from typing import List, Tuple

import PyPDF2
import pandas as pd
from PyPDF2.utils import PdfReadError
from colorama import Fore, Style, init

warnings.filterwarnings("ignore")


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


def cut_index(df: pd.DataFrame):
    """The index of the dataframe are filepaths. This function will determine the n first characters
    common to all lines and will remove them. In the end it will add a slash before each index. For
    example, ['/home/test/foo/bar.pdf', '/home/test/pdf.pdf'] will transform into
    ['/foo/bar.pdf', '/pdf.pdf'].

    Args:
        df (pd.DataFrame): dataframe to change the index from.

    """
    index = [x for x in df.axes[0]]

    if len(index) == 1:
        df.index = df.index.map(os.path.basename)
        df.index = df.index.map(lambda x: '/' + x)
        return

    i = 1
    keep_going = True
    delete = ''
    while keep_going:
        delete = index[0][:i]
        for k, _ in enumerate(index):
            if delete != index[k][:i]:
                keep_going = False
                break
        i += 1

    delete = delete[:-1]

    delete = delete.replace('\\', '/')
    delete = delete[:delete.rfind('/') + 1]

    df.index = df.index.map(lambda x: x.replace(delete, ''))
    df.index = df.index.map(lambda x: '/' + x)


# noinspection PyPep8Naming
@dataclass
class PDF:
    """Basic representation of a pdf file."""
    filename: str
    pages: int = field(init=False)
    height: int = field(init=False)
    width: int = field(init=False)

    def __post_init__(self):
        self.update_pages()

    def update_pages(self):
        """Opens the pdf to determine the number of pages."""
        fh = open(self.filename, 'rb')
        reader = PyPDF2.PdfFileReader(fh)

        try:
            self.pages = reader.getNumPages()
        except PdfReadError as e:
            print(Fore.RED + self.filename, '--', e)
            print(Style.RESET_ALL, end='')
            self.pages = 0
            self.height = -1
            self.width = -1
            return

        _, _, b, a = reader.getPage(0).mediaBox
        self.height = int(float(a) * 2.54 / 72)
        self.width = int(float(b) * 2.54 / 72)
        fh.close()

    def is_A4(self):
        """Determines if the pdf is an A4 format according to its dimensions."""
        return 28 <= self.height <= 30 and 20 <= self.width <= 22

    def is_A4_inverted(self):
        """Determines if the pdf is an A4 inverted format according to its dimensions."""
        return 28 <= self.width <= 30 and 20 <= self.height <= 22

    def is_slide(self):
        """Determines if the pdf is an slide format according to its dimensions."""
        return (24 <= self.width <= 26 and 18 <= self.height <= 20) or (
            32 <= self.width <= 34 and 18 <= self.height <= 20)

    def get_type(self) -> str:
        """Determines the type of the document.

        Returns:
            str: type of the document.
        """
        if self.is_A4():
            return 'A4'
        elif self.is_A4_inverted():
            return 'A4 inverted'
        elif self.is_slide():
            return 'slide'
        return 'unknown'


def get_file_list(path: str = './', exclude=None) -> list:
    """Given a directory path, it will scan and will return a list of all the filenames with its
    path.

    Args:
        path (str): path to scan.
        exclude (str): basic pattern to exclude filenames.

    Returns:
        list: list of all the filenames.
    """
    filenames = []
    for elem in os.walk(path):
        filenames += [os.path.join(elem[0], x).replace('\\', '/') for x in elem[2]]

    if exclude is not None:
        filenames = [x for x in filenames if exclude not in x]

    filenames.sort()

    return filenames


def get_pdfs(path: str = './', exclude=None) -> List[PDF]:
    """Returns a list of PDF instances of the pdfs found in the path folder and subfolders.

    Args:
        path (str): path to scan
        exclude (str): basic pattern to exclude filenames.

    Returns:
        List[PDF]: list of PDF instances.

    """
    filenames = get_file_list(path=path, exclude=exclude)
    filenames = [x for x in filenames if 'test_files' not in x and 'compact_pdf.pdf' not in x]
    pdfs = [PDF(f) for f in filenames if f.endswith('.pdf')]
    return pdfs


def concat_pdfs(path='./', output='compact_pdf.pdf', exclude=None) -> Tuple[List[PDF], List[PDF]]:
    """Given a path, it scans the path recursively to find pdf files, and combines all of them into
    the output. If a pdf has a number of pages odd, it will add a blank page at the end. If the
    format of a pdf isn't identified as 'A4', it will skip it.

    Args:
        path (str): path to find pdf files.
        output (str): path of the output pdf.
        exclude (str): basic pattern to exclude filenames.

    Returns:
        Tuple[List[PDF], List[PDF]]: A tuple of 2 items:
            * List of the PDF instances that were process successfully.
            * List of the PDF instances that raised any kind of Exception.

    """
    output_pdf = PyPDF2.PdfFileWriter()
    pdfs = get_pdfs(path=path, exclude=exclude)
    errors = []
    success = []

    for pdf in pdfs:
        pdf_type = pdf.get_type()

        if pdf_type != 'A4':
            errors.append(pdf)
            continue

        reader = PyPDF2.PdfFileReader(pdf.filename)

        for n in range(pdf.pages):
            page = reader.getPage(n)
            output_pdf.addPage(page)

        if pdf.pages % 2 != 0:
            output_pdf.addBlankPage()

        success.append(pdf)

    with open(output, 'wb') as f:
        output_pdf.write(f)

    return success, errors


def create_bugdet(path: str = './',
                  price_per_sheet: float = 0.03, exclude=None) -> Tuple[pd.DataFrame, List[PDF]]:
    """It scans recursively the path given searching pdf files, and will calculate the printing
    price of each of the pdf files found by multiplying price_per_sheet with the number of pages
    detected in the pdf. It will sum up all the data and will return it as a pd.DataFrame.

    Args:
        path (str): path to scan.
        price_per_sheet (float): price per sheet.
        exclude (str): basic pattern to exclude filenames.

    Returns:
        pd.DataFrame: dataframe with the filename as index, and the number of pages and the price
            as columns. The last row is the 'total' row.

    """
    pdfs = get_pdfs(path=path, exclude=exclude)
    df = pd.DataFrame(columns=['filename', 'pages', 'price'])
    df.set_index(['filename'], inplace=True)

    errors = []

    for pdf in pdfs:
        if pdf.get_type() != 'A4':
            errors.append(pdf)
            continue

        df.loc[pdf.filename] = (pdf.pages, pdf.pages * price_per_sheet)

    cut_index(df)

    df.sort_values(['pages'], inplace=True, ascending=False)
    df.loc['Total'] = df.loc[:, 'pages'].sum(), df.loc[:, 'price'].sum()
    df.loc[:, 'pages'] = df.loc[:, 'pages'].astype(int)

    return df, errors


def concat_pdfs_interface(path='./', output='compact_pdf.pdf', open_files=True, exclude=None):
    """Interface for concat_pdfs(). First it will safely delete the output file. Then it will
    search and concat the pdf files found. Finally, it will print the errors and the success. If
    open_files is True, it will open the first 5 error files.

    Args:
        path (str): path to scan.
        output (str): output of the result pdf file.
        open_files (bool): open the first 5 error files or not.
        exclude (str): basic pattern to exclude filenames.
    """
    print()
    safe_delete(output)

    success, errors = concat_pdfs(path=path, output=output, exclude=exclude)

    for pdf in errors:
        print(Fore.RED + f'TypeError: {pdf.get_type()!r} -- {pdf.filename!r}')

    for pdf in success:
        print(Fore.GREEN + f'Added: {pdf.filename!r}')

    print(Style.RESET_ALL, end='')

    print('-' * 30)
    print(f'Done:  {output!r}')

    adobe_path = 'C:/Program Files (x86)/Adobe/Acrobat DC/Acrobat/Acrobat.exe'

    if not open_files:
        return

    for pdf in errors[:5]:
        os.system(f'start "{adobe_path}" "{pdf.filename}" > nul')


def create_budget_interface(path='./', price_per_sheet=0.03, exclude=None):
    """Interface for create_budget(). First will search and concat the pdf files found. Then, it
    will print the errors and the success. Finally, the budget will be printed.

    Args:
        path (str): path to scan.
        price_per_sheet (float): price per sheet.
        exclude (str): basic pattern to exclude filenames.

    """
    df, errors = create_bugdet(path=path, price_per_sheet=price_per_sheet, exclude=exclude)

    for pdf in errors:
        print(Fore.RED + f'TypeError: {pdf.get_type()!r} -- {pdf.filename!r}')

    print(Style.RESET_ALL, end='')
    print()
    print(df)


def parse_args(args: List[str] = None) -> argparse.Namespace:
    """ArgumentParser designed for this application.

    Args:
        args (List[str]): list of arguments.

    Returns:
        argparse.Namespace: arguments processed.

    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('PDF')
    parser.add_argument('--exclude', type=str, default=None)
    subparsers = parser.add_subparsers()

    budget = subparsers.add_parser('budget')
    budget.add_argument('--path', type=str, default='./')
    budget.add_argument('--price', type=float, default=0.03)

    concat = subparsers.add_parser('concat')
    concat.add_argument('--output', type=str, default='compact_pdf.pdf')
    concat.add_argument('--no_open', action='store_false')
    concat.add_argument('--path', type=str, default='./')

    opt = parser.parse_args(args)
    if 'output' in opt:
        if opt.output.endswith('.pdf') is False:
            opt.output = opt.output + '.pdf'

    return opt


def main():
    """Main function."""
    if len(sys.argv) == 1:
        sys.argv.append('budget')

    opt = parse_args()
    init()

    if 'price' in opt:
        return create_budget_interface(path=opt.path, price_per_sheet=opt.price,
                                       exclude=opt.exclude)
    elif 'output' in opt:
        return concat_pdfs_interface(path=opt.path, output=opt.output, open_files=opt.no_open,
                                     exclude=opt.exclude)
    else:
        raise argparse.ArgumentError('Unknown error')


if __name__ == '__main__':
    main()
