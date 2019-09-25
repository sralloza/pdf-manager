import os
from typing import List, Tuple

import PyPDF2
from colorama import Fore, Style

from pdf_manager.core.core import PdfTypes, PDF
from pdf_manager.core.utils import get_pdfs, safe_delete

_PdL = List[PDF]
_C = Tuple[_PdL, _PdL]

__all__ = ['concat_pdfs']

def _concat_pdfs(path='./', output='compact_pdf.pdf', exclude=None) -> _C:
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

        if pdf_type != PdfTypes.A4:
            errors.append(pdf)
            continue

        reader = PyPDF2.PdfFileReader(pdf.filepath.as_posix())

        for n in range(pdf.pages):
            page = reader.getPage(n)
            output_pdf.addPage(page)

        if pdf.pages % 2 != 0:
            output_pdf.addBlankPage()

        success.append(pdf)

    with open(output, 'wb') as f:
        output_pdf.write(f)

    return success, errors


def concat_pdfs(path='./', output='compact_pdf.pdf', open_files=True, exclude=None):
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

    success, errors = _concat_pdfs(path=path, output=output, exclude=exclude)

    for pdf in errors:
        print(Fore.RED + f'TypeError: {pdf.get_type()!r} -- {pdf.filepath}')

    for pdf in success:
        print(Fore.GREEN + f'Added: {pdf.filepath}')

    print(Style.RESET_ALL, end='')

    print('-' * 30)
    print(f'Done:  {output!r}')

    adobe_path = 'C:/Program Files (x86)/Adobe/Acrobat DC/Acrobat/Acrobat.exe'

    if not open_files:
        return

    for pdf in errors[:5]:
        os.system(f'start "{adobe_path}" "{pdf.filepath}" > nul')
