from dataclasses import field, dataclass
from enum import Enum
from pathlib import Path
from typing import Union

import PyPDF2
from PyPDF2.utils import PdfReadError
from colorama import Fore, Style

from pdf_manager.core.exceptions import PdfError

_SoP = Union[str, Path]

__all__ = ['PdfTypes', 'PDF']


class PdfTypes(Enum):
    A4 = 0
    A4_inverted = 1
    slide = 2
    unknown = 3


@dataclass
class PDF:
    """Basic representation of a pdf file."""
    filepath: _SoP
    pages: int = field(default=None)
    height: int = field(default=None)
    width: int = field(default=None)

    def __post_init__(self):
        self.filepath = Path(self.filepath)
        self.update_pages()

    def update_pages(self):
        """Opens the pdf to determine the number of pages."""
        with self.filepath.open('rb') as fh:
            reader = PyPDF2.PdfFileReader(fh)

            try:
                self.pages = reader.getNumPages()
            except PdfReadError as e:
                print(Fore.RED + self.filepath, '--', e)
                print(Style.RESET_ALL, end='')
                self.pages = 0
                self.height = -1
                self.width = -1
                return

            heights = set()
            widths = set()
            for i in range(reader.getNumPages()):
                _, _, b, a = reader.getPage(i).mediaBox
                height = int(float(a) * 2.54 / 72)
                width = int(float(b) * 2.54 / 72)
                heights.add(height)
                widths.add(width)

            if len(heights) != 1:
                raise PdfError('Difference in heights: %r' % heights)

            if len(widths) != 1:
                raise PdfError('Difference in widths: %r' % widths)

            self.height = heights.pop()
            self.width = widths.pop()

    def is_A4(self) -> bool:
        """Determines if the pdf is an A4 format according to its dimensions."""
        return 28 <= self.height <= 30 and 20 <= self.width <= 22

    def is_A4_inverted(self) -> bool:
        """Determines if the pdf is an A4 inverted format according to its dimensions."""
        return 28 <= self.width <= 30 and 20 <= self.height <= 22

    def is_slide(self) -> bool:
        """Determines if the pdf is an slide format according to its dimensions."""
        return (24 <= self.width <= 26 and 18 <= self.height <= 20) or (
                32 <= self.width <= 34 and 18 <= self.height <= 20)

    def get_type(self) -> PdfTypes:
        """Determines the type of the document.

        Returns:
            str: type of the document.
        """
        if self.is_A4():
            return PdfTypes.A4
        elif self.is_A4_inverted():
            return PdfTypes.A4_invertedç
        elif self.is_slide():
            return PdfTypes.slide
        return PdfTypes.unknown
