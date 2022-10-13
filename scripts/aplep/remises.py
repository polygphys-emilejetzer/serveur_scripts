# -*- coding: utf-8 -*-
"""Créé le Mon Oct  3 09:42:23 2022 par emilejetzer."""

import re

from pathlib import Path

from polygphys.outils.reseau.courriel import Messagerie, CourrielsTableau
from polygphys.outils.config import FichierConfig
from polygphys.outils.reseau import DisqueRéseau


def main():
    dossier = Path('~').expanduser() / 'Volumes' / 'APLEP'
    infos = Path('~').expanduser() / 'Desktop' / 'aplep_k.txt'
    url, nom, mdp = [l.strip() for l in infos.open().read().split('\n')]

    with DisqueRéseau(url, dossier, 'K', nom, mdp) as disque:
        config = disque / 'Comités' / 'SPAM' / 'Listes' / \
            'Rapports de remise' / 'entrée_automatique.cfg'
        config = FichierConfig(config)

        messagerie = Messagerie(config)

        # TODO obtenir la pièce jointe et la sauvegarder
        messagerie.select('Comités/SPAM/Listes/Rapport de remises')
        for m in messagerie:
            for pj in m.pièces_jointes:
                print(pj.nom, pj.type_MIME)


if __name__ == '__main__':
    main()
