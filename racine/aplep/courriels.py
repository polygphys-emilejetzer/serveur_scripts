# -*- coding: utf-8 -*-
"""Créé le Thu Sep  8 14:38:42 2022 par emilejetzer."""

import os
import sys
import itertools
import time

import email.message
import email.parser
import email.policy

from functools import partial
from pathlib import Path
from datetime import datetime
from imaplib import IMAP4_SSL
from typing import Any

import getpass
import quopri
import dateutil.parser
import chardet
import schedule
import pandas
import keyring

from polygphys.outils.config import FichierConfig
from polygphys.outils.base_de_donnees import BaseTableau
from polygphys.serveur.racine.canari import créer_journal, noter_exceptions
from polygphys.outils.reseau import DisqueRéseau

journal = créer_journal(__name__, __file__)
horaire = schedule.every(10).minutes

CONFIGURATION_PAR_DÉFAUT: str = '''
[messagerie]
adresse = 
nom = 

[db]
adresse = 
'''


class CourrielsConfig(FichierConfig):

    def default(self) -> str:
        return CONFIGURATION_PAR_DÉFAUT


class Courriel:

    def __init__(self, message: email.message.Message):
        self.message = message

    @property
    def contenu(self):
        contenu = self.message.get_body(('plain', 'html', 'related'))

        if contenu is None:
            contenu = f'{contenu!r}'
        else:
            contenu = contenu.get_payload()

        if contenu.isascii():
            contenu = quopri.decodestring(contenu.encode('utf-8'))

            encodings = ('utf-8',
                         'cp1252',
                         chardet.detect(contenu)['encoding'])
            for encoding in encodings:
                try:
                    contenu = contenu.decode(encoding)
                except UnicodeDecodeError:
                    journal.exception(f'{encoding} ne fonctionne pas.')
                else:
                    break

        if isinstance(contenu, bytes):
            contenu = str(contenu, encoding='utf-8')

        contenu = contenu.replace('\r', '\n')
        while '\n\n\n' in contenu:
            contenu = contenu.replace('\n\n', '\n')

        return contenu

    @property
    def date(self) -> datetime:
        return dateutil.parser.parse(self['Date'], ignoretz=True)

    def __getitem__(self, clé: Any) -> Any:
        return self.message[clé]

    def __setitem__(self, clé: Any, val: Any):
        self.message[clé] = val

    @staticmethod
    def nettoyer_nom(nom: str) -> str:
        for c in ':, )(.?![]{}#/\\':
            nom = nom.replace(c, '_')
        while '__' in nom:
            nom = nom.replace('__', '_')

        nom = nom.strip('_')

        return nom

    @property
    def name(self) -> str:
        sujet: str = self['Subject']\
            .encode('ascii', 'ignore')\
            .decode('utf-8')\
            .strip()

        sujet = self.nettoyer_nom(sujet)

        return sujet + '.md'

    @property
    def parent(self) -> Path:
        nom = self.message.get('Thread-Topic', self.name[:-3])
        nom = self.nettoyer_nom(nom)

        for prefix, f in itertools.product(('fwd', 're', 'tr', 'ré'),
                                           (str.upper,
                                            str.lower,
                                            str.capitalize,
                                            str.title,
                                            str)):
            nom = nom.replace(f(prefix), '')

        return Path(nom)

    @property
    def path(self):
        return self.parent / self.name

    def __str__(self):
        return f'''- - - 
Date: {self.date.isoformat()}
De: {self['From']}
À: {self['To']}
Sujet: {self['Subject']}

{self.contenu}
'''

    def sauver(self, dossier: Path):
        chemin = dossier / self.path

        if not chemin.parent.exists():
            chemin.parent.mkdir()
        if not chemin.exists():
            chemin.touch()

        with chemin.open('w', encoding='utf-8') as f:
            f.write(str(self))


class Messagerie:

    def __init__(self, config: CourrielsConfig):
        if isinstance(config, (str, Path)):
            self.config = CourrielsConfig(config)
        else:
            self.config = config

        self._mdp = None

    @property
    def adresse(self):
        return self.config.get('messagerie', 'adresse')

    @property
    def nom(self):
        return self.config.get('messagerie', 'nom')

    @property
    def mdp(self):
        mdp_sys = keyring.get_password('system',
                                       nom := f'courriels.{self.nom}')
        if self._mdp is None and mdp_sys is None:
            self._mdp = getpass.getpass('mdp>')
            keyring.set_password('system', nom, self._mdp)
        elif self._mdp is None:
            self._mdp = keyring.get_password('system', nom)

        return self._mdp

    def message(self, serveur: IMAP4_SSL, numéro: str) -> Courriel:
        typ, data = serveur.fetch(numéro, '(RFC822)')
        message = email.parser.BytesParser(policy=email.policy.default)\
            .parsebytes(bytes(data[0][1]))

        return Courriel(message)

    def messages(self) -> Courriel:
        with IMAP4_SSL(self.adresse) as serveur:
            serveur.noop()
            serveur.login(self.nom, self.mdp)
            serveur.enable('UTF-8=ACCEPT')
            serveur.select()  # TODO: permettre de sélectionner d'autres boîtes
            typ, data = serveur.search(None, 'ALL')
            messages: list[str] = data[0].split()
            f = partial(self.message, serveur)

            yield from map(f, messages)

    def __iter__(self):
        return self.messages()

    @property
    def df(self) -> pandas.DataFrame:
        return pandas.DataFrame([[c.date,
                                  c['Subject'],
                                  c['From'],
                                  c['To'],
                                  c.parent.name] for c in self],
                                columns=('date',
                                         'sujet',
                                         'de',
                                         'a',
                                         'chaine'))


class CourrielsTableau(BaseTableau):

    def __init__(self, config: CourrielsConfig):
        if isinstance(config, (str, Path)):
            self.config = CourrielsConfig(config)
        else:
            self.config = config

        db = self.config.get('db', 'adresse')
        table = 'courriels'

        super().__init__(db, table)

    def ajouter_messagerie(self, messagerie: Messagerie):
        courriels_actuels = self.df
        nouveaux_courriels = messagerie.df

        lim_db = 1000
        nouveaux_courriels.a = nouveaux_courriels.a.map(
            lambda x: x[:lim_db])
        nouveaux_courriels.sujet = nouveaux_courriels.sujet.map(
            lambda x: x[:lim_db])
        nouveaux_courriels.chaine = nouveaux_courriels.chaine.map(
            lambda x: x[:lim_db])

        tous_courriels = pandas.concat([courriels_actuels,
                                        nouveaux_courriels])
        nouveaux_courriels = tous_courriels.drop_duplicates(keep=False)

        self.append(nouveaux_courriels)


@noter_exceptions(journal)
def main():
    dossier = Path('~').expanduser() / 'Volumes' / 'APLEP'
    infos = Path('~').expanduser() / 'Desktop' / 'aplep_k.txt'
    url, nom, mdp = [l.strip()
                     for l in infos.open().read().split('\n')]
    with DisqueRéseau(url, dossier, 'K', nom, mdp) as disque:
        journal.info('Charger la configuration...')
        config = disque / 'Exécutif' / 'V-pAA' / \
            'Courriels' / 'config_courriels_aplep.config'
        config = CourrielsConfig(config)
        print(config)

        journal.info('Configurer la messagerie et la base de données...')
        messagerie = Messagerie(config)
        tableau = CourrielsTableau(config)

        journal.info('Ajouter les nouveaux messages...')
        tableau.ajouter_messagerie(messagerie)
        journal.info('Messages ajoutés.')

        journal.info('Ajouter les messages...')
        for message in messagerie.messages():
            message.sauver(disque / 'Exécutif' / 'V-pAA' / 'Notes_K' /
                           'Exécutif' / 'VPAA' / 'Courriels')
        journal.info('Messages sauvegardés.')


def html(chemin: Path):
    with chemin.open('w') as fichier:
        print('<html>',
              '    <head>',
              f'        <title>{__name__} à {__file__}</title>',
              '    </head>',
              '    <body>',
              f'        <h1>{__name__} à {__file__}</h1>',
              f'        <p>Fonctionnel à {datetime.isoformat(datetime.now())}.</p>',
              '        <hr/>',
              f'        <h1>{chemin.with_suffix(".log")}</h1>',
              f'        <pre>{chemin.with_suffix(".log").open("r").read()}</pre>',
              '    </body>',
              '</html>',
              sep='\n',
              file=fichier)


if __name__ == '__main__':
    main()
