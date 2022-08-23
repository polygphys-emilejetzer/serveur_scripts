# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import logging

from pathlib import Path
from typing import Callable
from functools import wraps
from datetime import datetime

import schedule


FMT_JOURNAL = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)r'
DTFMT_JOURNAL = '%Y-%m-%d %H:%M'


def créer_journal(nom: str, chemin: str) -> logging.Logger:
    journal: logging.Logger = logging.getLogger(nom)
    journal.setLevel(logging.DEBUG)
    chemin: Path = Path(chemin).with_suffix('.log')
    chemin.touch()
    handler = logging.FileHandler(chemin, encoding='utf-8')
    fmter = logging.Formatter(fmt=FMT_JOURNAL, datefmt=DTFMT_JOURNAL)
    handler.setFormatter(fmter)
    handler.setLevel(logging.DEBUG)
    journal.addHandler(handler)

    return journal


def noter_exceptions(journal: logging.Logger) -> Callable:

    def f(fonction: Callable) -> Callable:

        @wraps(fonction)
        def F(*args, **kargs):
            try:
                fonction(*args, **kargs)
            except Exception:
                journal.exception('Une erreur s\'est produite.')
                raise

        return F

    return f


# Script (modèle)

journal = créer_journal(__name__, __file__)
horaire = schedule.every(10).minutes


@noter_exceptions(journal)
def main():
    journal.info('Ça marche.')


def html(chemin: Path):
    with chemin.open('w') as fichier:
        print('<html>',
              '    <head>',
              f'        <title>{__name__} à {__file__}</title>',
              '    </head>',
              '    <body>',
              f'        <h1>{__name__} à {__file__}</h1>',
              f'        <p>Fonctionnel à {datetime.isoformat(datetime.now())}.</p>',
              '        <hr/>',
              f'        <h1>{chemin.with_suffix(".log")}</h1>',
              f'        <pre>{chemin.with_suffix(".log").open("r").read()}</pre>',
              '    </body>',
              '</html>',
              sep='\n',
              file=fichier)


if __name__ == '__main__':
    main()
