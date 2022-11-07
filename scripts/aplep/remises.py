# -*- coding: utf-8 -*-
"""Créé le Mon Oct  3 09:42:23 2022 par emilejetzer."""

import re

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

from polygphys.outils.reseau.courriel import Messagerie, CourrielsTableau
from polygphys.outils.config import FichierConfig
from polygphys.outils.reseau import DisqueRéseau
from polygphys.outils.base_de_donnees import BaseTableau


def main():
    dossier = Path('~').expanduser() / 'Volumes' / 'APLEP'
    infos = Path('~').expanduser() / 'Desktop' / 'aplep_k.txt'
    url, nom, mdp = [l.strip() for l in infos.open().read().split('\n')]

    with DisqueRéseau(url, dossier, 'K', nom, mdp) as disque:
        chemin_config = disque / 'Comités' / 'SPAM' / 'Listes' / \
            'Rapports de remise' / 'entrée_automatique.cfg'
        config = FichierConfig(chemin_config)

        messagerie = Messagerie(config)
        tableau = BaseTableau(config.get('db', 'adresse'),
                              'remises',
                              index_col='id')

        # TODO obtenir la pièce jointe et la sauvegarder
        messagerie.select('Comités/SPAM/Listes/Rapport de remises')
        for m in messagerie:
            for pj in m.pièces_jointes:
                if 'CSV' in pj.nom or 'csv' in pj.nom:
                    colonnes = []
                    sec, sections = None, [[], []]
                    contenu = str(pj.contenu, encoding='iso-8859-10')
                    for i, ligne in enumerate(contenu.split('\n')):
                        if ligne.startswith('EPLNUMMAT'):
                            colonnes += ligne.strip().strip(';').split(';')
                            sec = 0
                        elif sec == 0 and ligne.startswith('RCECOD_2'):
                            colonnes += ligne.strip().strip(';').split(';')
                            sec = 1
                        elif sec == 1 and ligne.startswith('CS_DECOMPTE_EPLNUMMAT'):
                            break
                        elif sec is not None:
                            ligne = ligne.strip().replace(',', '.').strip(';').split(';')
                            sections[sec].append(ligne)

                    contenu = []
                    for un, deux in zip(*sections):
                        contenu.append(un + deux)

                    df = pd.DataFrame(contenu, columns=colonnes)
                    df.loc[:, 'date'] = m.date

                    tableau.append(df)

                    chemin_pj = chemin_config.parent / pj.nom.lower()
                    if chemin_pj not in chemin_pj.parent.glob('*.csv'):
                        df.to_csv(chemin_pj)


if __name__ == '__main__':
    main()
