import argparse
import sys
from typing import List

from colorama import init

from pdf_manager.budget import create_budget
from pdf_manager.concat import concat_pdfs

_LS = List[str]

__all__ = ['main']

def _parse_args(args: _LS = None) -> argparse.Namespace:
    """ArgumentParser designed for this application.

    Args:
        args (List[str]): list of arguments.

    Returns:
        argparse.Namespace: arguments processed.

    """
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser('PDF')
    parser.add_argument('--exclude', type=str, default=None,
                        metavar='pattern', help='regex pattern to exclude documents')

    subparsers = parser.add_subparsers(title='commands', dest='command')
    subparsers.required = True

    # TODO: add help for each argument and each parser
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

    opt = _parse_args()
    init()

    if opt.command == 'budget':
        return create_budget(path=opt.path, price_per_sheet=opt.price,
                             exclude=opt.exclude)
    elif opt.command == 'concat':
        return concat_pdfs(path=opt.path, output=opt.output, open_files=opt.no_open,
                           exclude=opt.exclude)
    else:
        raise exit('Unknown error')


if __name__ == '__main__':
    main()
