# -*- coding: utf-8 -*-
"""Créé le Tue Sep 20 11:03:31 2022 par emilejetzer."""

from pathlib import Path

from polygphys.serveur import WebScriptConfig
from polygphys.outils.journal import Repository


def main():
    répertoire_journaux = Path('./journaux/')
    répertoire_modèles = Path('./modèles/')
    répertoire_config = Path('./config/')

    # Configuration de base
    print('[script]')
    nom_de_script = input('nom> ')
    chemin_de_script = input('chemin (relatif)> ')
    fonction_à_exécuter = input('fonction> ')

    chemin_config = (répertoire_config / nom_de_script).with_suffix('.cfg')
    script_config = WebScriptConfig(chemin_config)
    script_config.set('script', 'nom', nom_de_script)
    script_config.set('script', 'chemin', chemin_de_script)
    script_config.set('script', 'fonction', fonction_à_exécuter)

    # Journalisation
    print('[journal]')

    répertoire_journal = répertoire_journaux / nom_de_script
    chemin_journal = (répertoire_journal /
                      nom_de_script).with_suffix('.sqlite')
    adresse = f'sqlite:///{chemin_journal}'

    script_config.set('journal', 'adresse', str(adresse))
    script_config.set('journal', 'répertoire', str(répertoire_journal))

    répertoire_journal.mkdir()
    chemin_journal.touch()

    git = Repository(répertoire_journal)
    git.init()
    git.add(chemin_journal.name)
    git.commit('Premier commit.')

    # Modèle HTML
    print('[html]')
    print('modèles disponibles:')
    for m in répertoire_modèles.glob('*.html'):
        print(m.name)
    nom_modèle = input('nom du fichier> ')

    chemin_modèle = répertoire_modèles / nom_modèle

    script_config.set('html', 'modèle', str(chemin_modèle))

    # Programmation horaire
    print('[horaire]')
    intervalle = input('intervalle> ')
    unité = input('nom de fonction d\'unité du module schedule> ')
    à = input('moment dans l\'intervalle pour l\'exécution> ')

    if intervalle == '':
        intervalle = 1
    else:
        intervalle = int(intervalle)

    if unité == '':
        unité = 'hours'

    if à == '':
        à = ':00'

    script_config.set('horaire', 'intervalle', str(intervalle))
    script_config.set('horaire', 'unité', unité)
    script_config.set('horaire', 'à', à)


if __name__ == '__main__':
    main()
