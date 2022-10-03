# -*- coding: utf-8 -*-
"""Créé le Thu Sep  8 14:38:42 2022 par emilejetzer."""

from pathlib import Path

from polygphys.outils.reseau import DisqueRéseau
from polygphys.outils.reseau.courriel import CourrielsConfig, Messagerie, CourrielsTableau


def main():
    dossier = Path('~').expanduser() / 'Volumes' / 'APLEP'
    infos = Path('~').expanduser() / 'Desktop' / 'aplep_k.txt'
    url, nom, mdp = [l.strip()
                     for l in infos.open().read().split('\n')]
    with DisqueRéseau(url, dossier, 'K', nom, mdp) as disque:
        config = disque / 'Exécutif' / 'V-pAA' / \
            'Courriels' / 'config_courriels_aplep.config'
        config = CourrielsConfig(config)

        messagerie = Messagerie(config)
        tableau = CourrielsTableau(config)

        tableau.ajouter_messagerie(messagerie)

        for message in messagerie.messages():
            message.sauver(disque / 'Exécutif' / 'V-pAA' / 'Notes_K' /
                           'Exécutif' / 'VPAA' / 'Courriels')


if __name__ == '__main__':
    main()
