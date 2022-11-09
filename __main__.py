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
lecteur_arguments.add_argument('config', default=str(CONFIG), required=False)
arguments = lecteur_arguments.parse_args()

main(arguments.config)
