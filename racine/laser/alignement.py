# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import logging

from pathlib import Path
from datetime import datetime

import schedule

from canari import créer_journal, noter_exceptions

from polygphys.sst.inscriptions_sst.inscriptions_sst import SSTSIMDUTInscriptionConfig, SSTSIMDUTInscriptionForm
from polygphys.outils.reseau import OneDrive


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

chemin_config = Path('~').expanduser() / 'simdut.cfg'
config = SSTSIMDUTInscriptionConfig(chemin_config)

dossier = OneDrive('',
                   config.get('onedrive', 'organisation'),
                   config.get('onedrive', 'sous-dossier'),
                   partagé=True)
fichier = dossier / config.get('formulaire', 'nom')
config.set('formulaire', 'chemin', str(fichier))

formulaire = SSTSIMDUTInscriptionForm(config)

# Script (modèle)

journal = créer_journal(__name__, __file__)
horaire = schedule.every(10).minutes


@noter_exceptions(journal)
def main():
    maintenant = datetime.now()
    if maintenant.weekday() == 4 \
            and maintenant.hour in (13, 14):
        logger.info('Mise à jour...')
        try:
            formulaire.mise_à_jour()
            logger.info('Mise à jour complétée.')
        except Exception:
            logger.exception('Erreur!')
            raise


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
