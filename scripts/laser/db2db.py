# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import logging

import pandas as pd

from pathlib import Path
from datetime import datetime

import schedule

from polygphys.outils.base_de_donnees import BaseTableau
from polygphys.outils.config import FichierConfig
from polygphys.outils.reseau import OneDrive

FICHIER_CONFIG = Path('~').expanduser() / 'laser_db2db.cfg'


def main():
    config = FichierConfig(FICHIER_CONFIG)

    adresse = config.get('db', 'adresse')
    nom_origine = config.get('transfert', 'origine')
    index_col = config.get('db', 'index')
    tableau_origine = BaseTableau(adresse, nom_origine, index_col=index_col)

    noms_destinations = config.getlist('transfert', 'destination')
    tableaux_destinations = [BaseTableau(tableau_origine.db,
                                         nom,
                                         index_col=index_col)
                             for nom in noms_destinations]

    for nom in noms_destinations:
        destination = BaseTableau(tableau_origine.db,
                                  nom,
                                  index_col=index_col)
        colonnes = {y: x for x, y in config[nom].items()}
        nouveaux = tableau_origine.select(list(colonnes.values()))\
            .rename(colonnes)

        toutes = pd.concat([destination.df, nouveaux])\
            .drop_duplicates(subset=['matricule'],
                             keep='first')\
            .dropna(subset='matricule')

        print(nom)
        print(toutes.head())

        destination.màj(toutes)


if __name__ == '__main__':
    main()
