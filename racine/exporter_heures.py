# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import datetime
import time
import logging

from pathlib import Path

import getpass
import keyring
import schedule

import pandas as pd

from polygphys.outils.reseau import DisqueRéseau
from polygphys.outils.journal import Repository

from polygphys.admin.heures.heures import FeuilleDeTempsConfig, FeuilleDeTemps

SORTIE = Path(__file__).with_suffix('.txt')
logger = logging.getLogger(__name__)
handler = logging.FileHandler(SORTIE, encoding='utf-8')
fmter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(message)s',
                          datefmt='%Y-%m-%d %H:%M')
handler.setFormatter(fmter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def exporter(d: DisqueRéseau,
             config: FeuilleDeTempsConfig,
             feuille_de_temps: FeuilleDeTemps):
    logger.info('Montage du disque au point %s', d.chemin)
    git = Repository(d.chemin)

    fichier_excel = next(d.chemin.glob(config.get('export', 'fichier')))
    logger.info()

    condition = feuille_de_temps.db.table(
        'heures').columns.exporte == False
    nouvelles_entrées = feuille_de_temps.select(where=[condition])

    colonnes = config.getlist('export', 'db')
    à_exporter = nouvelles_entrées.loc[:, colonnes]
    conversions = config['conversion']
    à_exporter = à_exporter.rename(columns=conversions)

    if not à_exporter.empty:
        colonnes = config.getlist('export', 'xlsx')
        ajouts = filter(lambda x: x not in à_exporter.columns, colonnes)

        for colonne in ajouts:
            if colonne in config['export'].keys():
                à_exporter.loc[:, colonne] = config.get('export', colonne)
            else:
                à_exporter.loc[:, colonne] = None

        à_exporter = à_exporter.loc[:, colonnes]

        vieilles_entrées = pd.read_excel(fichier_excel)
        toutes_entrées = pd.concat((vieilles_entrées, à_exporter),
                                   ignore_index=True)\
            .sort_values(by=['Date', 'Payeur', 'Demandeur'])\
            .reset_index(drop=True)

        toutes_entrées.to_excel(fichier_excel,
                                sheet_name=f'feuille de temps {datetime.date.today()}',
                                index=False)

        nouvelles_entrées.loc[:, 'exporte'] = True
        git.add(str(fichier_excel))

        feuille_de_temps.update(nouvelles_entrées)
        git.commit(f'Màj automatisée le {datetime.datetime.now()}')


def charger_config(config: FeuilleDeTempsConfig):
    adresse = config.get('bd', 'adresse')
    logger.debug('Adresse de la base de données: %s', adresse)

    feuille_de_temps = FeuilleDeTemps(adresse)
    logger.debug('Objet «feuille de temps»: %s', feuille_de_temps)

    url = config.get('export', 'disque')
    logger.debug('Disque d\'exportation: %s', url)

    chemin = Path(config.get('export', 'montage')).expanduser()
    logger.debug('Chemin de montage: %s', chemin)

    nom = config.get('export', 'nom')
    logger.debug('Nom de connexion: %s', nom)

    logger.info('Obtention du mot de passe du disque réseau...')
    mdp = keyring.get_password('system', f'exporter_heures_{nom}')
    if mdp is None:
        mdp = getpass.getpass('mdp: ')
        keyring.set_password('system', f'exporter_heures_{nom}', mdp)
    logger.info('Mot de passe obtenu et sauvegardé.')

    return url, chemin, nom, mdp, feuille_de_temps


def fonction():
    chemin = Path('~/Documents/Polytechnique/Heures').expanduser()
    config = FeuilleDeTempsConfig(chemin / 'heures.cfg')
    url, chemin, nom, mdp, feuille_de_temps = charger_config(config)
    with DisqueRéseau(url, chemin, 'J', nom, mdp) as d:
        exporter(d, config, feuille_de_temps)


def main():
    try:
        fonction()
    except Exception:
        logger.exception('Une erreur s\'est produite.')
