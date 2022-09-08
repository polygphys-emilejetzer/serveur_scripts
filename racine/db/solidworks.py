# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

from pathlib import Path

import schedule

from datetime import datetime

from polygphys.serveur.racine.canari import créer_journal, noter_exceptions

from polygphys.admin.inventaire.zotero.zotero import MigrationConfig, ZoteroItems


# Script (modèle)

journal = créer_journal(__name__, __file__)
horaire = schedule.every(10).minutes


@noter_exceptions(journal)
def main():
    pass


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
