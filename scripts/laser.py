# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import subprocess

from pathlib import Path
from datetime import datetime

from polygphys.sst.certificats_laser.nouveau_certificats import SSTLaserCertificatsConfig, SSTLaserCertificatsForm
from polygphys.outils.reseau import OneDrive


def main():
    chemin_config = Path('~').expanduser() / 'certificats_laser.cfg'
    config = SSTLaserCertificatsConfig(chemin_config)
    dossier = OneDrive('',
                       config.get('onedrive', 'organisation'),
                       config.get('onedrive', 'sous-dossier'),
                       partagé=True)
    fichier = dossier / config.get('formulaire', 'nom')
    config.set('formulaire', 'chemin', str(fichier))
    formulaire = SSTLaserCertificatsForm(config)

    try:
        exporteur = subprocess.Popen(['unoconv', '--listener'])
        formulaire.mise_à_jour()
    finally:
        exporteur.terminate()


if __name__ == '__main__':
    main()
