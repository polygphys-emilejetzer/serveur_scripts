# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

from pathlib import Path

from polygphys.sst.inscriptions_sst.inscriptions_sst import SSTSIMDUTInscriptionConfig
from polygphys.outils.reseau import OneDrive
from polygphys.outils.reseau.msforms import MSFormExportBD


def main():
    chemin_config = Path('~').expanduser() / 'laser_form2db.cfg'
    config = SSTSIMDUTInscriptionConfig(chemin_config)

    dossier = OneDrive('',
                       config.get('onedrive', 'organisation'),
                       config.get('onedrive', 'sous-dossier'),
                       partagé=True)
    fichier = dossier / config.get('formulaire', 'nom')
    config.set('formulaire', 'chemin', str(fichier))
    formulaire = MSFormExportBD(config)
    formulaire.mise_à_jour()


if __name__ == '__main__':
    main()
