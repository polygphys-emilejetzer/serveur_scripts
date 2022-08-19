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


logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdin)
fmter = logging.Formatter(fmt='[%(asctime)s] %(levelname)s: %(message)s',
                          datefmt='%Y-%m-%d %H:%M')
handler.setFormatter(fmter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def script_handler(racine: Path, chemins: set[Path]):

    class ScriptHTTPRequestHandler(SimpleHTTPRequestHandler):

        def __init__(self, request, client_address, server):
            directory = racine
            super().__init__(request, client_address, server, directory=directory)

        def do_GET(self):
            chemin = Path(self.directory) / self.path[1:]
            sortie = chemin.with_suffix('.txt') if chemin.name else chemin

            if chemin in chemins and sortie.exists():
                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                with sortie.open('rb') as f:
                    doc = f.read()
                    self.send_header('Content-length', len(doc))
                    self.end_headers()
                    self.wfile.write(doc)
            else:
                super().do_GET()

    return ScriptHTTPRequestHandler


class Serveur(ThreadingHTTPServer):

    def __init__(self,
                 racine: str,
                 chemins: tuple[str],
                 server_address: tuple[str, int] = ('', 8000)):
        super().__init__(server_address, script_handler(racine, chemins))

    def __call__(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            raise
        finally:
            self.server_close()


def update(serveur: Serveur, modules: set, racine: Path):
    # Noms des fichiers et modules existants
    chemins = set(c for c in racine.glob('*.py'))
    noms = set(x.stem for x in chemins)

    # Retirer les modules non-existants
    modules -= set(module for module in modules if module.__name__ not in noms)

    # Recharger les modules pré-existants
    modules |= set(map(reload, modules))

    # Importer les nouveaux modules
    vieux_noms = set(module.__name__ for module in modules)
    modules |= set(map(import_module, vieux_noms))

    # Programmer les fonctions
    schedule.clear()
    for module in modules:
        module.logger.addHandler(handler)
        schedule.every().hour.do(module.main)

    # Mettre à jour le serveur
    serveur.RequestHandlerClass = script_handler(racine, chemins)


def stop(thread: Thread, serveur: Serveur):
    serveur.server_close()
    thread.join(5)
    schedule.clear()


def loop(serveur: Serveur, modules: set, racine: Path):
    update(serveur, modules, racine)
    thread = Thread(target=serveur)
    try:
        thread.start()  # Démarrer le serveur
        schedule.run_all()  # Rouler toutes les fonctions une première fois

        # Programmer la mise à jour des modules
        schedule.every().day.at('01:30').do(update, serveur, modules, racine)

        # Rouler les fonctions au besoin
        # Le serveur roule dans une autre thread
        while True:
            schedule.run_pending()
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop(thread, serveur)
        return input('Continuer? [oui|*] ') == 'oui'
    finally:
        stop(thread, serveur)

    return False


def main():
    racine = Path('./racine').resolve()
    modules = set()
    serveur = Serveur(str(racine), set())
    vieux_path = sys.path[:]
    try:
        sys.path.append(str(racine))
        while loop(serveur, modules, racine):
            continue
    finally:
        sys.path = vieux_path[:]


if __name__ == '__main__':
    main()
