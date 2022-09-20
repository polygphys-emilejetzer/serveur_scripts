# -*- coding: utf-8 -*-"""Serveur d'exécution de scripts programmés.Créé le Thu Sep  8 13:59:06 2022 par emilejetzer."""import timeimport loggingimport importlibimport jsonimport sysfrom pathlib import Pathfrom typing import Callablefrom functools import wraps, cached_property, partialfrom datetime import datetimefrom threading import Threadfrom http.server import ThreadingHTTPServer, SimpleHTTPRequestHandlerimport schedulefrom polygphys.outils.config import FichierConfigfrom polygphys.outils.journal import Journalfrom polygphys.outils.base_de_donnees import BaseTableauclass WebScriptConfig(FichierConfig):    def default(self):        return '''[script]    nom =     chemin =     fonction = [horaire]    intervalle =     unité = [journal]    adresse =     répertoire = [html]    modèle = '''class WebScript:    def __init__(self, config: WebScriptConfig):        if isinstance(config, (str, Path)):            self.config = WebScriptConfig(config)        else:            self.config = config        tableau = BaseTableau(self.adresse, self.nom)        self.journal = Journal(logging.DEBUG, self.répertoire, tableau)        self.logger.addHandler(self.journal)    @property    def nom(self) -> str:        return self.config.get('script', 'nom')    @property    def script(self) -> Path:        return Path(self.config.get('script', 'chemin'))    @property    def adresse(self) -> str:        return self.config.get('journal', 'adresse')    @property    def répertoire(self):        return self.config.get('journal', 'répertoire')    @property    def fonction(self) -> Callable:        return getattr(self.module, self.config.get('script', 'fonction'))    @property    def intervalle(self) -> int:        return self.config.getint('horaire', 'intervalle', fallback=1)    @property    def unité(self) -> str:        return self.config.get('horaire', 'unité', fallback='hours')    @property    def à(self):        return self.config.get('horaire', 'à', fallback=':00')    @property    def modèle(self) -> str:        chemin = self.config.get('html', 'modèle')        return open(chemin, encoding='utf-8').read()    def load(self):        self.logger.info('Exécution de load() pour %s', self.nom)        spec = importlib.util.spec_from_file_location(self.nom, self.script)        self.logger.debug('%r', spec)        module = importlib.util.module_from_spec(spec)        self.logger.debug('%r', module)        spec.loader.exec_module(module)        self.module = module        self.logger.debug('%r', self.module)    def reload(self):        self.logger.info('Exécution de reload() pour %s', self.nom)        importlib.reload(self.module)    def getLogger(self):        return logging.getLogger(self.nom)    @property    def logger(self):        return self.getLogger()    def __call__(self, *args, **kargs):        self.logger.info('Exécution de %s', self.nom)        fct = partial(self.fonction, *args, **kargs)        thread = Thread(target=fct)        thread.start()        thread.join()    def programmer(self):        self.logger.info('Programmation de %s', self.nom)        self.logger.debug('Aux %s %s', self.intervalle, self.unité)        self.jobid = getattr(schedule.every(self.intervalle),                             self.unité)\            .at(self.à)\            .do(self)        self.logger.debug('Avec jobid %s', self.jobid)    def annuler(self):        schedule.cancel_job(self.jobid)    def __str__(self):        self.logger.info('Affichage de %s', self.nom)        return self.modèle.format(script=self)    def json(self):        objet = {'script': {'nom': self.nom,                            'chemin': str(self.script),                            'fonction': self.fonction.__name__},                 'horaire': {'intervalle': self.intervalle,                             'unité': self.unité},                 'journal': {'adresse': self.adresse,                             'répertoire': self.répertoire},                 'html': {'modèle': self.modèle}}        return json.dumps(objet)class ScriptServeurConfig(FichierConfig):    def default(self):        return '''[scripts]    canari = config/canari.config[serveur]    adresse = localhost:8888    racine = racine/'''class ScriptServeur(ThreadingHTTPServer):    def __init__(self, config: ScriptServeurConfig):        if isinstance(config, (str, Path)):            self.config = ScriptServeurConfig(config)        else:            self.config = config        adresse, port = self.config\            .get('serveur', 'adresse')\            .split(':')        super().__init__((adresse, int(port)), ScriptHTTPRequestHandler)    @cached_property    def scripts(self):        return {script.script: script                for script in (WebScript(config)                               for nom, config in self.config.items('scripts'))}    @property    def racine(self):        return Path(self.config.get('serveur', 'racine'))    def update(self):        # On s'asssure de créer l'attribut s'il n'a pas été appelé encore        self.scripts        # On efface l'attribut de cache        del self.scripts        # On rappelle la propriété pour reconstruire le cache        self.scripts    def __call__(self):        try:            thread = Thread(target=self.serve_forever)            thread.start()            for script in self.scripts.values():                script.load()                script.programmer()            while True:                schedule.run_pending()                time.sleep(1)        except KeyboardInterrupt:            logging.exception('Fin du programme par l\'utilisateur.')        except Exception:            logging.exception(                'Une erreur s\'est produite pendant l\'exécution du serveur.')        finally:            self.shutdown()            schedule.clear()            thread.join(1)class ScriptHTTPRequestHandler(SimpleHTTPRequestHandler):    def __init__(self, request, client_adress, server):        self.serveur = server        super().__init__(request, client_adress, server)    @property    def chemin(self):        chemin = self.path.lstrip('/')        return Path(chemin)    def do_GET(self):        logging.debug('Accès à %s', self.chemin)        if self.chemin in self.serveur.scripts:            script = self.serveur.scripts[self.chemin]            try:                message = bytes(str(script), encoding='utf-8')            except Exception as erreur:                message = bytes(                    f'Erreur {erreur} dans la tentative d\'exécuter {self.path}.',                    encoding='utf-8')                logging.exception(message)                script.logger.exception(message)                self.send_response(502, message)                self.send_header(                    'Content-type', 'text/plain; charset=utf-8')                self.send_header('Content-length', len(message))                self.end_headers()                self.wfile.write(message)            else:                self.send_response(200)                self.send_header(                    'Content-type', 'text/html; charset=utf-8')                self.send_header('Content-length', len(message))            finally:                self.end_headers()                self.wfile.write(message)        elif self.serveur.racine in self.chemin.parents\                or self.serveur.racine == self.chemin:            super().do_GET()        else:            message = bytes('Ce répertoire n\'est pas accessible.',                            encoding='utf-8')            self.send_response(401, message)            self.send_header(                'Content-type', 'text/plain; charset=utf-8')            self.send_header('Content-length', len(message))            self.end_headers()            self.wfile.write(message)    def do_POST(self):        if self.chemin in self.serveur.scripts:            try:                message = self.serveur.scripts[self.chemin].json()            except Exception as erreur:                message = f'Erreur {erreur} dans la tentative d\'exécuter {self.path}.'                logging.exception(message)                self.send_response(502, message)                self.send_header(                    'Content-type', 'text/plain; charset=utf-8')                self.send_header('Content-length', len(message))                self.end_headers()                self.wfile.write(message)            else:                self.send_response(200)                self.send_header(                    'Content-type', 'text/plain; charset=utf-8')                self.send_header('Content-length', len(message))            finally:                self.end_headers()                self.wfile.write(message)        else:            message = 'Erreur 418: Je ne suis pas une cafetière, mais je ne peux quand même pas accomplir ce que vous me demandez.'            self.send_response(418, message)            self.send_header('Content-type', 'text/plain; charset=utf-8')            self.send_header('Content-length', len(message))            self.end_headers()            self.wfile.write(message)def main():    logging.basicConfig(stream=sys.stdout,                        level=logging.DEBUG)    serveur = ScriptServeur('serveur.cfg')    serveur()if __name__ == '__main__':    main()