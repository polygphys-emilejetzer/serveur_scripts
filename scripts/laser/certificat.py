# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 14:15:04 2022 par emilejetzer."""

import logging
import subprocess
import keyring
import getpass
import shutil

from pathlib import Path
from datetime import datetime

from polygphys.sst.inscriptions_sst.inscriptions_sst import SSTSIMDUTInscriptionConfig, SSTSIMDUTInscriptionForm
from polygphys.outils.reseau import OneDrive, DisqueRéseau
from polygphys.outils.config import FichierConfig
from polygphys.sst.certificats_laser.nouveau_certificats import Certificat
from polygphys.outils.base_de_donnees import BaseTableau


def main():
    chemin_config = Path('~').expanduser() / 'laser_certificat.cfg'
    config = FichierConfig(chemin_config)

    chemin_modèle = Path(__file__).parent / 'Certificat Formation Laser.pptx'
    certificat = Certificat(chemin_modèle)

    adresse = config.get('db', 'adresse')
    tableau = config.get('db', 'tableau')
    index_col = config.get('db', 'index')
    tableau = BaseTableau(adresse, tableau, index_col)

    cadre = tableau.df
    for i, rangée in cadre.loc[cadre.ppt != True,
                               ['matricule', 'nom']].iterrows():
        matricule, nom = rangée.matricule, rangée.nom

        try:
            certificat.màj(nom, matricule)
            certificat.cert.save(f'{matricule}.pptx')
        except Exception:
            raise
        else:
            cadre.loc[i, 'ppt'] = True
    tableau.màj(cadre)

    try:
        exporteur = subprocess.Popen(['unoconv', '--listener'])
        cadre = tableau.df
        for i, rangée in cadre.loc[(cadre.ppt == True) & (cadre.pdf != True),
                                   ['matricule', 'nom']].iterrows():
            matricule, nom = rangée.matricule, rangée.nom
            ppt, pdf = f'{matricule}.pptx', f'{nom} {matricule}.pdf'
            try:
                subprocess.run(['unoconv', '-f', 'pdf', '-o', pdf, ppt])
            except Exception:
                raise
            else:
                Path(ppt).unlink()
                cadre.loc[i, 'pdf'] = True
        tableau.màj(cadre)
    finally:
        exporteur.terminate()

    disques = {}
    for disque in config.getlist('certificats', 'disques'):
        url = config.get(disque, 'url')
        chemin = config.getpath(disque, 'mount_point')
        drive = config.get(disque, 'drive')
        nom_disque = config.get(disque, 'nom')
        mode = config.get(disque, 'method')

        mdp = keyring.get_password(
            'system', f'polygphys.sst.laser.{disque}.{nom_disque}')
        if mdp is None:
            mdp = getpass.getpass('mdp: ')
            keyring.set_password(
                'system', f'polygphys.sst.laser.{disque}.{nom_disque}', mdp)

        disques[disque] = DisqueRéseau(url,
                                       chemin,
                                       drive,
                                       nom_disque,
                                       mdp,
                                       mode)

    cadre = tableau.df
    for i, rangée in cadre.loc[(cadre.pdf == True) & (cadre.envoye != True),
                               ['matricule', 'nom']].iterrows():
        try:
            for nom_disque, disque in disques.items():
                with disque as d:
                    nom_fichier = Path(f'{rangée.nom} {rangée.matricule}.pdf')
                    destination = d /\
                        config.get(nom_disque, 'chemin', fallback='.')
                    shutil.copy(nom_fichier, destination)
        except Exception:
            raise
        else:
            nom_fichier.unlink()
            cadre.loc[i, 'envoye'] = True
    tableau.màj(cadre)


if __name__ == '__main__':
    main()
