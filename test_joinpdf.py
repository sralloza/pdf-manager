import os
from shutil import copy

import PyPDF2
import pytest

from pdf_manager import get_file_list, get_pdfs, concat_pdfs, create_budget
from pdf_manager.core import PdfTypes, PDF
from pdf_manager.main import parse_args


class Memory:
    dummy_a4 = ''
    dummy_a4_inverted = ''
    dummy_slide = ''
    tmp_path = ''


@pytest.fixture(scope='session', autouse=True)
def load_pdfs(tmp_path_factory):
    Memory.tmp_path = tmp_path_factory.getbasetemp().as_posix()

    Memory.dummy_a4 = os.path.join(Memory.tmp_path, 'dummy-a4.pdf')
    Memory.dummy_a4_inverted = os.path.join(Memory.tmp_path, 'dummy-a4-inverted.pdf')
    Memory.dummy_slide = os.path.join(Memory.tmp_path, 'dummy-slide.pdf')

    copy('test_files/dummy-a4.pdf', Memory.dummy_a4)
    copy('test_files/dummy-a4-inverted.pdf', Memory.dummy_a4_inverted)
    copy('test_files/dummy-slide.pdf', Memory.dummy_slide)


class TestConcatPdf:

    def test_get_file_list(self):
        file_list = get_file_list(path=Memory.tmp_path)
        file_list = [os.path.basename(x) for x in file_list]
        file_list = [x for x in file_list if not x.startswith('.')]

        assert file_list == ['dummy-a4-inverted.pdf', 'dummy-a4.pdf', 'dummy-slide.pdf']

    def test_get_pdfs(self):
        pdfs = get_pdfs(path=Memory.tmp_path)
        assert isinstance(pdfs, list)
        assert isinstance(pdfs[0], PDF)

    def test_a4(self):
        p = PDF(Memory.dummy_a4)
        assert p.get_type() == PdfTypes.A4

    def test_slide(self):
        p = PDF(Memory.dummy_slide)
        assert p.get_type() == PdfTypes.slide

    def test_a4_inverted(self):
        p = PDF(Memory.dummy_a4_inverted)
        assert p.get_type() == PdfTypes.A4_inverted

    def test_concat_pdfs(self):
        output = os.path.join(Memory.tmp_path, 'compact_pdf.pdf')
        success, errors = concat_pdfs(path=Memory.tmp_path, output=output)

        reader = PyPDF2.PdfFileReader(output)
        assert reader.getNumPages() == 2
        assert len(success) == 1
        assert len(errors) == 2


def test_budget():
    df, errors = create_budget(path=Memory.tmp_path, price_per_sheet=0.03)
    assert len(errors) == 2

    assert '               pages  price' in str(df)
    assert 'filepath' in str(df)
    assert '/dummy-a4.pdf      1   0.03' in str(df)
    assert 'Total              1   0.03' in str(df)


class TestParser:
    def test_budget(self):
        with pytest.raises(SystemExit, match='2'):
            parse_args()

        opt = parse_args(f'budget --path {Memory.tmp_path}'.split())
        assert opt.path == Memory.tmp_path
        assert opt.price == 0.03
        assert 'output' not in opt
        assert 'no_open' not in opt

        opt = parse_args('budget --price 0.01'.split())
        assert opt.path == './'
        assert opt.price == 0.01
        assert 'output' not in opt
        assert 'no_open' not in opt

        opt = parse_args(f'budget --path {Memory.tmp_path} --price 0.05'.split())
        assert opt.path == Memory.tmp_path
        assert opt.price == 0.05
        assert 'output' not in opt
        assert 'no_open' not in opt

    def test_concat(self):
        with pytest.raises(SystemExit, match='2'):
            parse_args()

        opt = parse_args(f'concat --path {Memory.tmp_path}'.split())
        assert opt.path == Memory.tmp_path
        assert opt.output == 'compact_pdf.pdf'
        assert opt.no_open is True

        opt = parse_args('concat --output test.pdf'.split())
        assert opt.path == './'
        assert opt.output == 'test.pdf'
        assert opt.no_open is True

        opt = parse_args('concat --no_open'.split())
        assert opt.path == './'
        assert opt.output == 'compact_pdf.pdf'
        assert opt.no_open is False

        opt = parse_args(f'concat --path {Memory.tmp_path} --output test.pdf'.split())
        assert opt.path == Memory.tmp_path
        assert opt.output == 'test.pdf'
        assert opt.no_open is True

        opt = parse_args(f'concat --path {Memory.tmp_path} --no_open'.split())
        assert opt.path == Memory.tmp_path
        assert opt.output == 'compact_pdf.pdf'
        assert opt.no_open is False

        opt = parse_args(f'concat --output test.pdf --path {Memory.tmp_path}'.split())
        assert opt.path == Memory.tmp_path
        assert opt.output == 'test.pdf'
        assert opt.no_open is True

        opt = parse_args(f'concat --output test.pdf --no_open'.split())
        assert opt.path == './'
        assert opt.output == 'test.pdf'
        assert opt.no_open is False

        opt = parse_args(f'concat --no_open --path {Memory.tmp_path}'.split())
        assert opt.path == Memory.tmp_path
        assert opt.output == 'compact_pdf.pdf'
        assert opt.no_open is False

        opt = parse_args(f'concat --no_open --output test.pdf'.split())
        assert opt.path == './'
        assert opt.output == 'test.pdf'
        assert opt.no_open is False

        opt = parse_args(f'concat --path {Memory.tmp_path} --output test.pdf --no_open'.split())
        assert opt.path == Memory.tmp_path
        assert opt.output == 'test.pdf'
        assert opt.no_open is False


if __name__ == '__main__':
    pytest.main([os.path.basename(__file__), '-v'])
