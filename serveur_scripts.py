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


def script_handler(racine: Path, chemins: tuple[Path]):

    class ScriptHTTPRequestHandler(SimpleHTTPRequestHandler):

        def __init__(self, request, client_address, server):
            directory = racine
            super().__init__(request, client_address, server, directory=directory)

        def do_GET(self):
            chemin = Path(self.directory) / self.path[1:]

            if chemin.name:
                sortie = chemin.with_suffix('.txt')
            else:
                sortie = chemin

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
            pass
        finally:
            self.server_close()


def main():
    racine = Path('./racine').resolve()

    chemins = [c for c in racine.glob('*.py')]
    serveur = Serveur(str(racine), chemins)

    vieux_path = sys.path[:]
    try:
        sys.path.append(str(racine))
        noms = [x.stem for x in racine.glob('*.py')]
        logger.debug('noms = %s', noms)

        modules = [import_module(x) for x in noms]
        logger.debug('modules = %s', modules)

        fonctions = [module.main for module in modules]
        logger.debug('fonctions = %s', fonctions)

        thread = Thread(target=serveur)
        logger.debug('thread = %s', thread)

        def update():
            chemins = [c for c in racine.glob('*.py')]
            nouveau_handler = script_handler(racine, chemins)
            serveur.RequestHandlerClass = nouveau_handler

            fichiers_python = [x.stem for x in racine.glob('*.py')]
            nouveaux_noms = [x for x in fichiers_python if x not in noms]
            anciens_noms = [x for x in noms if x not in fichiers_python]

            anciens_index = [noms.index(x) for x in anciens_noms]
            for i in anciens_index[::-1]:
                modules.pop(i)

            modules[:] = [reload(module) for module in modules]

            for nn in nouveaux_noms:
                modules.append(import_module(nn))

            fonctions[:] = [module.main for module in modules]

        def stop():
            serveur.server_close()
            thread.join()

        schedule.every().day.at('01:30').do(update)

        for fonction in fonctions:
            schedule.every().hour.do(fonction)

        try:
            logger.info('Démarrer le serveur...')
            thread.start()
            logger.info('Serveur démarré.')

            logger.info('Exécuter les fonctions une première fois...')
            for fonction in fonctions:
                logger.debug('%s', fonction)
                fonction()

            logger.info('Début de la boucle...')
            while True:
                schedule.run_pending()
                time.sleep(0.5)
            logger.info('Fin de la boucle.')
        except KeyboardInterrupt:
            logger.info('Sortie volontaire.')
        finally:
            logger.info('On ferme tout...')
            stop()
            logger.info('Le serveur est fermé.')
    finally:
        sys.path = vieux_path[:]


if __name__ == '__main__':
    main()
