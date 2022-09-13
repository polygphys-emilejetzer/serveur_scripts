# -*- coding: utf-8 -*-
"""Créé le Thu Sep  8 13:59:06 2022 par emilejetzer."""

import logging
import importlib
import json

from pathlib import Path
from typing import Callable
from functools import wraps
from datetime import datetime

import schedule

from polygphys.outils.config import FichierConfig
from polygphys.outils.journal import Journal
from polygphys.outils.base_de_donnees import BaseTableau

FMT_JOURNAL = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)r'
DTFMT_JOURNAL = '%Y-%m-%d %H:%M'


def créer_journal(nom: str, chemin: str) -> logging.Logger:
    journal: logging.Logger = logging.getLogger(nom)
    journal.setLevel(logging.DEBUG)
    chemin: Path = Path(chemin).with_suffix('.log')
    chemin.touch()
    handler = logging.FileHandler(chemin, encoding='utf-8')
    fmter = logging.Formatter(fmt=FMT_JOURNAL, datefmt=DTFMT_JOURNAL)
    handler.setFormatter(fmter)
    handler.setLevel(logging.DEBUG)
    journal.addHandler(handler)

    return journal


def noter_exceptions(journal: logging.Logger) -> Callable:

    def f(fonction: Callable) -> Callable:

        @wraps(fonction)
        def F(*args, **kargs):
            try:
                fonction(*args, **kargs)
            except Exception:
                journal.exception('Une erreur s\'est produite.')
                raise

        return F

    return f


class WebScriptConfig(FichierConfig):

    def default(self):
        return '''[script]
    nom = 
    chemin = 
    fonction = 

[horaire]
    intervalle = 
    unité = 

[journal]
    adresse = 
    répertoire = 

[html]
    modèle = 
'''


class WebScript:

    def __init__(self, config: WebScriptConfig):
        if isinstance(config, (str, Path)):
            self.config = WebScriptConfig(config)
        else:
            self.config = config

        tableau = BaseTableau(self.adresse, self.nom)
        self.journal = Journal(logging.DEBUG, self.répertoire, tableau)

    @property
    def nom(self) -> str:
        return self.config.get('script', 'nom')

    @property
    def script(self) -> Path:
        return Path(self.config.get('script', 'chemin'))

    @property
    def adresse(self) -> str:
        return self.config.get('journal', 'adresse')

    @property
    def fonction(self) -> Callable:
        return getattr(self.module, self.config.get('script', 'fonction'))

    @property
    def intervalle(self) -> int:
        return self.config.getint('horaire', 'intervalle')

    @property
    def unité(self) -> str:
        return self.config.get('horaire', 'unité')

    @property
    def modèle(self) -> str:
        chemin = self.config.get('html', 'modèle')
        return open(chemin, encoding='utf-8').read()

    def load(self):
        spec = importlib.util.spec_from_file_location(self.nom, self.script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.module = module

    def reload(self):
        importlib.reload(self.module)

    def getLogger(self):
        return logging.getLogger(self.nom)

    def __run__(self, *args, **kargs):
        self.fonction(*args, **kargs)

    def programmer(self):
        self.jobid = getattr(schedule.every(self.intervalle),
                             self.unité)\
            .do(self)

    def annuler(self):
        schedule.cancel_job(self.jobid)

    def __str__(self):
        return self.modèle.format(script=self)

    def json(self):
        objet = {'script': {'nom': self.nom,
                            'chemin': str(self.script),
                            'fonction': self.fonction.__name__},
                 'horaire': {'intervalle': self.intervalle,
                             'unité': self.unité},
                 'journal': {'adresse': self.adresse,
                             'répertoire': self.répertoire},
                 'html': {'modèle': self.modèle}}

        return json.dumps(objet)
