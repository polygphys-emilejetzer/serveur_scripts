# -*- coding: utf-8 -*-
"""Créé le Fri Sep 30 06:49:33 2022 par emilejetzer."""

import mechanize
import requests
import ssl
import getpass
import keyring

from http import cookiejar
from html.parser import HTMLParser
from datetime import datetime
from pathlib import Path

import html2text

import pandas as pd

from polygphys.outils.config import FichierConfig
from polygphys.outils.base_de_donnees import BaseTableau

EXTERNE = 'https://www.polymtl.ca/carriere/offres-demploi'
INTERNE = 'https://safirh.polymtl.ca/apex/polyp/f?p=121:313:8833031240742::NO:::'


class AffichagesParseur(HTMLParser):

    def __init__(self, externe=True, config=None, *args, **kargs):
        self.dans_un_lien = False
        self.config = config
        self.externe = externe

        if externe:
            self.préfixe_liens = 'https://www.polymtl.ca'
        else:
            self.préfixe_liens = 'https://safirh.polymtl.ca/apex/polyp/'

        self.affichages = []
        super().__init__(*args, **kargs)

    @property
    def interne(self):
        return not self.externe

    @property
    def df(self):
        df = pd.DataFrame(self.affichages)
        return df

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if all((self.interne,
                tag == 'a',
                attrs.get('class') == 'sofUrl',
                attrs.get('href') != '')):
            self.dans_un_lien = True
            self.affichages.append(
                {'url': self.préfixe_liens + attrs.get('href')})
        elif all((tag == 'a',
                  str(attrs.get('href')).startswith('/carriere/offres-demploi/'))):
            self.dans_un_lien = True
            self.affichages.append(
                {'url': self.préfixe_liens + attrs.get('href')})

    def handle_endtag(self, tag):
        if tag == 'a' and self.dans_un_lien:
            self.dans_un_lien = False

    def handle_data(self, data):
        if self.dans_un_lien and data:
            if self.interne:
                numéro = data.split('-', 1)[0].strip()
                poste = data.split('-', 1)[1].split('(', 1)[0].strip()
                nature = data.split('(', 1)[1].split(')', 1)[0].strip()
                service = data.split(')', 1)[1].strip()
            elif self.externe:
                numéro = None
                if '(' in data:
                    nature = data.split('(', 1)[1].split(')', 1)[0].strip()
                    poste = data.split('(', 1)[0].strip()
                    service = data.split(')', 1)[1].strip()
                else:
                    nature = None
                    poste = data.split('-', 1)[0].strip()
                    service = data.split('-', 1)[0].strip()

            self.affichages[-1]['numéro'] = numéro
            self.affichages[-1]['poste'] = poste
            self.affichages[-1]['nature'] = nature
            self.affichages[-1]['service'] = service
            self.affichages[-1]['interne'] = self.interne
            self.affichages[-1]['date'] = datetime.now()\
                .isoformat()\
                .replace(':', '_')

    def ramper(self, adresse=EXTERNE, **kargs):
        self.pot_à_biscuits = cookiejar.CookieJar()
        self.navigateur = mechanize.Browser()
        self.navigateur.set_cookiejar(self.pot_à_biscuits)
        self.navigateur.set_handle_robots(False)

        en_têtes = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
        for c, v in en_têtes.items():
            self.navigateur.set_header(c, v)

        if self.interne:
            self.navigateur.open(adresse)
            lien = self.navigateur.find_link('Connexion')
            self.navigateur.follow_link(lien)
            lien = self.navigateur.find_link(
                "Vous êtes un employé de l'université ?")
            self.navigateur.follow_link(lien)

            self.navigateur.forms()
            self.navigateur.select_form(nr=0)
            self.navigateur.form['username'] = self.config.get('safirh', 'nom')
            self.navigateur.form['password'] = kargs.get('mdp', None)
            self.navigateur.submit()

            lien = self.navigateur.find_link('Emplois disponibles')
            self.navigateur.follow_link(lien)

        réponse = self.navigateur.open(adresse)
        réponse = str(réponse.read(), encoding='utf-8')
        self.feed(réponse)

    def contenu(self):
        for i, rangée in self.df.iterrows():
            réponse = self.navigateur.open(rangée.url)
            contenu = str(réponse.read(), encoding='utf-8')
            self.affichages[i]['contenu'] = contenu
            self.affichages[i]['contenu_md'] = html2text.html2text(contenu)


def main():
    chemin_config = Path('~').expanduser() / 'aplep_affichages.cfg'
    config = FichierConfig(chemin_config)

    tableau = BaseTableau(config.get('db', 'adresse'),
                          'affichages')

    nom = config.get('safirh', 'nom')
    mdp = keyring.get_password('system', nom := f'safirh.{nom}')
    if mdp is None:
        mdp = getpass.getpass('mdp>')
        keyring.set_password('system', nom, mdp)

    for externe, url in zip(map(bool, range(2)), (INTERNE, EXTERNE)):
        affichages = AffichagesParseur(externe=externe, config=config)
        affichages.ramper(url, mdp=mdp)
        affichages.contenu()

        tableau.append(affichages.df)


if __name__ == '__main__':
    main()
