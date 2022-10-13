# -*- coding: utf-8 -*-
"""Créé le Fri Sep 30 15:28:46 2022 par emilejetzer."""

import keyring
import getpass

from pathlib import Path

import pandas as pd
from typing import Any

from http import cookiejar
from html.parser import HTMLParser

import mechanize

from polygphys.outils.config import FichierConfig
from polygphys.outils.base_de_donnees import BaseTableau


class ParseurExterne(HTMLParser):

    def __init__(self, url: str):
        self.url = url

        super().__init__()

    def handle_starttag(self, tag: str, attrs: tuple[tuple[str, str]]):
        attrs = dict(attrs)

        if tag == 'div'\
                and 'pane-content' in attrs.get('class', ''):
            self.in_pane_content = True
        elif self.in_pane_content\
                and tag == 'h2':
            self.in_titre = True
        elif self.in_pane_content\
                and 'field-item' in attrs.get('class', ''):
            self.in_field_item = True

    def handle_endtag(self, tag: str):
        if self.in_titre and tag == 'h2':
            self.in_titre = False
        elif self.in_field_item and tag == 'div':
            self.in_field_item = False

    def handle_data(self, data: str):
        if self.in_titre:
            self.titre = data
        elif self.in_field_item and data.strip():
            self.field_items.append(data.strip())

    def lire(self) -> pd.Series:
        self.field_items = []
        self.in_pane_content, self.in_titre, self.in_field_item = False, False, False

        self.pot_à_biscuits = cookiejar.CookieJar()
        self.navigateur = mechanize.Browser()
        self.navigateur.set_cookiejar(self.pot_à_biscuits)
        self.navigateur.set_handle_robots(False)

        en_têtes = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        for c, v in en_têtes.items():
            self.navigateur.set_header(c, v)

        réponse = self.navigateur.open(self.url)
        réponse = str(réponse.read(), encoding='utf-8')
        self.feed(réponse)

        return pd.Series({'numéro': '',
                          'poste': '',
                          'nature': '',
                          'service': '',
                          'début': None,
                          'fin': None,
                          'durée_affichage': None,
                          'classe': None,
                          'rémunération_minimale': None,
                          'rémunération_maximale': None,
                          'date_limite': None})


class ParseurInterne(HTMLParser):

    def __init__(self, url: str):
        self.url = url

    def lire(self) -> pd.Series:
        pass


def détails_externe(affichage: pd.Series) -> pd.Series:
    pass


def détails_interne(affichage: pd.Series) -> pd.Series:
    pass


def main():
    chemin_config = Path('~').expanduser() / 'aplep_affichages.cfg'
    config = FichierConfig(chemin_config)

    tableau = BaseTableau(config.get('db', 'adresse'),
                          'affichages')

    # Affichages internes
    critères = [tableau.table.c.interne == False]
    affichages_externes = tableau.select(where=critères)\
        .drop_duplicates(subset=('url',), keep='last')

    for i, r in affichages_externes.iterrows():
        aff = ParseurExterne(r.url)
        aff.lire()
        print(aff.field_items[:5])


if __name__ == '__main__':
    main()
