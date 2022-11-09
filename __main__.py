# -*- coding: utf-8 -*-
"""Créé le Mon Sep 19 09:06:13 2022 par emilejetzer."""

import argparse

from pathlib import Path

from . import main

CONFIG = Path(__file__).parent / 'serveur.cfg'

lecteur_arguments = argparse.ArgumentParser(
    prog='Serveur de scripts horaires',
    description='Exécuter des scripts périodiquement et obtenir leur statut.',
    epilog='Contacter Émile Jetzer @ Polytechnique Montréal pour plus de détails.')
lecteur_arguments.add_argument(
    '-x', '--config', dest='config', default=str(CONFIG), required=False)
lecteur_arguments.add_argument(
    '-i', '--init', dest='init', default=False, required=False)


arguments = lecteur_arguments.parse_args()

if lecteur_arguments.init:
    config = lecteur_arguments.config
    if not config.exists():
        with CONFIG.open('r', encoding='utf-8') as original:
            with open(config, 'w', encoding='utf-8') as nouveau:
                nouveau.write(original.read())

    répertoire_journaux = Path('./journaux/')
    répertoire_modèles = Path('./modèles/')
    répertoire_config = Path('./config/')

    if not répertoire_journaux.exists():
        répertoire_journaux.mkdir()
    if not répertoire_modèles.exists():
        répertoire_modèles.mkdir()
    if not répertoire_config.exists():
        répertoire_config.mkdir()

    print('Il faut placer les scripts correctement dans les bons dossiers...')
else:
    main(arguments.config)
