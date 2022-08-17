# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import logging

from pathlib import Path

import sqlite3
import sqlalchemy

from polygphys.admin.inventaire.zotero.zotero import MigrationConfig, ZoteroItems


SORTIE = Path(__file__).with_suffix('.txt')
logger = logging.getLogger(__name__)
handler = logging.FileHandler(SORTIE, encoding='utf-8')
fmter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(message)s',
                          datefmt='%Y-%m-%d %H:%M')
logging.basicConfig(filename=SORTIE,
                    filemode='a',
                    encoding='utf-8')
handler.setFormatter(fmter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

journal = Path('~/zotero_a_inventaire.log').expanduser()
chemin = Path('~/zotero_a_inventaire.cfg').expanduser()
config = MigrationConfig(chemin)

zotero = config.get('zotero', 'adresse')
inventaire2022 = config.get('inventaire2022', 'adresse')
nom = config.get('inventaire2022', 'nom')
mdp = config.get('inventaire2022', 'mdp')

inventaire2022 = inventaire2022.format(nom=nom, mdp=mdp)


def main():
    try:
        logger.info('Mise à jour...')
        bd = ZoteroItems(zotero, inventaire2022)
        bd.charger()
    except (Exception, sqlite3.OperationalError, sqlalchemy.exc.OperationalError):
        logger.exception('Une erreur s\'est produite.')
