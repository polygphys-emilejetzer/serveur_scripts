# -*- coding: utf-8 -*-
"""Créé le Wed Aug 17 13:06:49 2022 par emilejetzer."""

import sys
import schedule
import time
import logging

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from importlib import import_module, reload
from threading import Thread
from functools import wraps
from typing import Callable

from polygphys.outils.config import FichierConfig

from polygphys.serveur.racine import WebScript, WebScriptConfig

# Journalisation
journal = logging.getLogger(__name__)
journal.setLevel(logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG)

fmter = logging.Formatter(fmt='%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s',
                          datefmt='%Y-%m-%d %H:%M')

handler = logging.StreamHandler()
handler.setFormatter(fmter)
handler.setLevel(logging.DEBUG)

chemin = Path(__file__).with_suffix('.log')
handler2 = logging.FileHandler(chemin, encoding='utf-8')
handler2.setFormatter(fmter)
handler2.setLevel(logging.INFO)

journal.addHandler(handler)
journal.addHandler(handler2)

racine = Path('racine')  # .resolve()

# Définitions importantes


def script_handler(racine: Path, chemins: set[Path], modules: set):

    class ScriptHTTPRequestHandler(SimpleHTTPRequestHandler):

        def __init__(self, request, client_address, server):
            directory = racine
            super().__init__(request, client_address, server, directory=directory)

        def do_GET(self):
            chemin = Path(self.directory) / self.path[1:]
            sortie = chemin.with_suffix('.html') if chemin.name else chemin
            module = list(filter(lambda x: Path(
                x.__file__) == chemin.resolve(), modules))

            if chemin in chemins and module:
                module = module[0]
                journal.debug('On accède à %s', module)

                module.html(sortie)
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')

                with sortie.open('rb') as f:
                    doc = f.read()
                    self.send_header('Content-length', len(doc))
                    self.end_headers()
                    self.wfile.write(doc)
                sortie.unlink()
            else:
                super().do_GET()

    return ScriptHTTPRequestHandler


def MetaScriptHTTPRequestHandler(config, scripts):

    class ScriptHTTPRequestHandler(SimpleHTTPRequestHandler):
        racine = racine
        scripts = scripts

        def __init__(self, request, client_address, server):
            super().__init__(request,
                             client_address,
                             server,
                             directory=str(self.racine))

        def do_GET(self):
            if self.path in self.scripts:
                try:
                    message = str(self.script[self.path])
                except Exception as erreur:
                    message = f'Erreur {erreur} dans la tentative d\'exécuter {self.path}.'
                    logging.exception(message)
                    self.send_response(502, message)
                    self.send_header(
                        'Content-type', 'text/plain; charset=utf-8')
                    self.send_header('Content-length', len(message))
                    self.end_headers()
                    self.wfile.write(message)
                else:
                    self.send_response(200)
                    self.send_header(
                        'Content-type', 'text/plain; charset=utf-8')
                    self.send_header('Content-length', len(message))
                finally:
                    self.end_headers()
                    self.wfile.write(message)
            else:
                super().do_GET()

        def do_POST(self):
            if self.path in self.scripts:
                try:
                    message = self.script[self.path].json()
                except Exception as erreur:
                    message = f'Erreur {erreur} dans la tentative d\'exécuter {self.path}.'
                    logging.exception(message)
                    self.send_response(502, message)
                    self.send_header(
                        'Content-type', 'text/plain; charset=utf-8')
                    self.send_header('Content-length', len(message))
                    self.end_headers()
                    self.wfile.write(message)
                else:
                    self.send_response(200)
                    self.send_header(
                        'Content-type', 'text/plain; charset=utf-8')
                    self.send_header('Content-length', len(message))
                finally:
                    self.end_headers()
                    self.wfile.write(message)
            else:
                message = 'Erreur 418: Je ne suis pas une cafetière, mais je ne peux quand même pas accomplir ce que vous me demandez.'
                self.send_response(418, message)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.send_header('Content-length', len(message))
                self.end_headers()
                self.wfile.write(message)

    return ScriptHTTPRequestHandler


class ScriptServeurConfig(FichierConfig):

    def default(self):
        return '''[scripts]
    nom = chemin_vers_config.config

[serveur]
    adresse = 
'''


class ScriptServeur(ThreadingHTTPServer):

    def __init__(self, config: ScriptServeurConfig):
        if isinstance(config, (str, Path)):
            self.config = ScriptServeurConfig(config)
        else:
            self.config = config

        adresse = self.config.get('serveur', 'adresse')
        super().__init__(adresse, self.créer_handler())

    @property
    def scripts(self):
        return {nom: WebScript(config)
                for nom, config in self.config.items('scripts')}

    def créer_handler(self):
        return MetaScriptHTTPRequestHandler(self.config, self.scripts)

    def __call__(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            raise
        finally:
            self.shutdown()


class Serveur(ThreadingHTTPServer):

    def __init__(self,
                 racine: str,
                 chemins: set[str],
                 modules: set,
                 server_address: tuple[str, int] = ('', 8000)):
        super().__init__(server_address, script_handler(racine, chemins, modules))

    def __call__(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            raise
        finally:
            self.shutdown()


def update(serveur: Serveur, modules: set, racine: Path):
    # Noms des fichiers et modules existants
    chemins = set(c for c in racine.glob('**/*.py'))
    noms = set(str(x.with_suffix('')).replace('/', '.')
               for x in chemins
               if not x.name.startswith('__'))

    # Retirer les modules non-existants
    modules -= set(module for module in modules if module.__name__ not in noms)

    # Recharger les modules pré-existants
    modules |= set(map(reload, modules))

    # Importer les nouveaux modules
    vieux_noms = set(module.__name__ for module in modules)
    nouveaux_noms = set(nom for nom in noms if nom not in vieux_noms)

    modules |= set(map(import_module, nouveaux_noms))

    # Programmer les fonctions
    schedule.clear()
    for module in modules:
        module.journal.addHandler(handler)
        schedule.repeat(module.horaire, module.main)
    journal.info('Horaire prêt.')

    # Mettre à jour le serveur
    serveur.RequestHandlerClass = script_handler(racine, chemins, modules)
    journal.info('Serveur mis à jour.')


def stop(thread: Thread, serveur: Serveur):
    serveur.shutdown()
    journal.info('serveur est fermé.')

    thread.join(1)
    journal.info('thread est rejointe.')

    schedule.clear()
    journal.info('L\'horaire est vide.')


def loop(serveur: Serveur, modules: set, racine: Path):
    update(serveur, modules, racine)
    journal.info('Mise à jour des modules')
    journal.info('%s', modules)

    thread = Thread(target=serveur)
    journal.info('thread créée pour le serveur: %s', thread)

    try:
        thread.start()  # Démarrer le serveur
        journal.info('thread démarrée.')

        # schedule.run_all()  # Rouler toutes les fonctions une première fois
        journal.info('Programmes roulés une première fois.')

        # Programmer la mise à jour des modules
        schedule.every().day.at('01:30').do(update, serveur, modules, racine)
        journal.info('Màj des modules programmée.')

        # Rouler les fonctions au besoin
        # Le serveur roule dans une autre thread
        while True:
            schedule.run_pending()
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop(thread, serveur)
        journal.info('On arrête.')

        return input('Continuer? [oui|*] ') == 'oui'
    except Exception:
        journal.exception('On arrête après une erreur sérieuse.')
        raise
    finally:
        stop(thread, serveur)
        journal.info('Tout est éteint.')

    return False


def avec_dossier(chemin: Path) -> Callable:

    def f(fonction: Callable) -> Callable:

        @wraps(fonction)
        def F(*args, **kargs):
            vieux_path = sys.path[:]
            try:
                sys.path.append(str(chemin))
                fonction(*args, **kargs)
            finally:
                sys.path = vieux_path[:]

        return F

    return f


@avec_dossier(racine)
def commencer_boucle(serveur, modules, racine):
    while loop(serveur, modules, racine):
        journal.info('On repart...')


def main():
    modules = set()
    serveur = Serveur(str(racine), set(), modules)
    journal.debug('serveur: %s', serveur)

    commencer_boucle(serveur, modules, racine)


if __name__ == '__main__':
    main()
