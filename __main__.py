# -*- coding: utf-8 -*-
"""Créé le Mon Sep 19 09:06:13 2022 par emilejetzer."""

import argparse

from pathlib import Path

from . import main

CONFIG = Path(__file__).parent / 'serveur.cfg'

lecteur_arguments = argparse.ArgumentParser(
    prog='serveur_script',
    description='Exécuter des scripts périodiquement et obtenir leur statut.',
    epilog='Contacter Émile Jetzer @ Polytechnique Montréal pour plus de détails.')
lecteur_arguments.add_argument(
    '-c', '--config', dest='config', default='./serveur.cfg', required=False)
lecteur_arguments.add_argument(
    '-i', '--init', dest='init', default=False, required=False, action='store_true')


arguments = lecteur_arguments.parse_args()

if arguments.init:
    config = Path(arguments.config)
    if not config.exists():
        with CONFIG.open('r', encoding='utf-8') as original:
            with config.open('w', encoding='utf-8') as nouveau:
                nouveau.write(original.read())

    répertoire_journaux = Path('./journaux/')
    répertoire_modèles = Path('./modèles/')
    répertoire_config = Path('./config/')
    répertoire_racine = Path('./racine/')

    if not répertoire_journaux.exists():
        répertoire_journaux.mkdir()
    if not répertoire_modèles.exists():
        répertoire_modèles.mkdir()
    if not répertoire_config.exists():
        répertoire_config.mkdir()
    if not répertoire_racine.exists():
        répertoire_racine.mkdir()

    print('Il faut placer les scripts correctement dans les bons dossiers...')
else:
    main(arguments.config)
