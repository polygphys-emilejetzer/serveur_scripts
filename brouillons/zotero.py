# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import logging

from pathlib import Path

from polygphys.admin.inventaire.zotero import script_zotero


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


def main():
    try:
        script_zotero.main()
    except Exception:
        logger.exception('Une erreur s\'est produite.')
