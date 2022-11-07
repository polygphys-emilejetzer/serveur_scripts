# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import getpass
import keyring

from subprocess import run
from pathlib import Path

from polygphys.outils.reseau import DisqueRéseau
from polygphys.outils.config import FichierConfig
from polygphys.outils.journal import Repository


def main():
    chemin = Path('~').expanduser() / 'obsidian_git.cfg'
    config = FichierConfig(chemin)
    
    for répertoire in config.getlist('git', 'répertoires'):
        # Modifications locales
        chemin_local = Path(config.get(répertoire, 'icloud')).expanduser()
        print(chemin_local)
        
        répertoire_local = Repository(chemin_local)
        
        # Répertoire distant
        adresse = config.get(répertoire, 'url')
        mount_point = Path(config.get(répertoire, 'mount_point')).expanduser()
        drive = config.get(répertoire, 'drive')
        nom = config.get(répertoire, 'nom')
        mode = config.get(répertoire, 'method')
        
        mdp = keyring.get_password('system', f'{adresse}-{nom}')
        if mdp is None:
            mdp = getpass.getpass(f'mdp {répertoire}:')
            keyring.set_password('system', f'{adresse}-{nom}', mdp)
        
        with DisqueRéseau(adresse, mount_point, drive, nom, mdp, mode) as d:
            chemin_distant = d / config.get(répertoire, 'chemin')
            print(chemin_distant)
            
            répertoire_distant = Repository(chemin_distant)
            
            #répertoire_local.pull()
            run(['git', 'pull', 'auto', 'master'], cwd=répertoire_local.path)
            répertoire_distant.pull()
            
            répertoire_local.add('.')
            répertoire_local.commit('Automatique.')
            #répertoire_distant.pull()
            run(['git', 'pull', 'auto', 'master'], cwd=répertoire_local.path)
            
            répertoire_distant.add('.')
            répertoire_distant.commit('Automatique.')
            #répertoire_local.pull()


if __name__ == '__main__':
    main()
