# -*- coding: utf-8 -*-
"""Créé le Fri Oct  7 11:37:44 2022 par emilejetzer."""


from pathlib import Path
from datetime import datetime, timedelta

from polygphys.admin.heures.heures import FeuilleDeTempsConfig, FeuilleDeTemps
from polygphys.outils.reseau.courriel import Courriel


def main():
    chemin = Path('~/Documents/Polytechnique/Heures').expanduser()
    config = FeuilleDeTempsConfig(chemin / 'heures.cfg')
    feuille_de_temps = FeuilleDeTemps(config.get('bd', 'adresse'))

    aujourdhui = datetime.today()
    décalage = timedelta(days=aujourdhui.weekday() + 1)
    dimanche = aujourdhui - décalage
    critères = (feuille_de_temps.table.c.date > dimanche,)
    résumé = feuille_de_temps.select(('date',
                                      'heures',
                                      'description',
                                      'payeur',
                                      'autres'),
                                     where=critères)
    résumé.date = résumé.date.map(lambda d: d.date())
    résumé = résumé.set_index('date')

    quotidien = résumé.groupby('date').sum('heures')

    stats = {'total': résumé.heures.sum()}

    message = '''Salut Émile, voici les heures que tu as rentrées cette semaine à date, n'oublie pas d'effectuer les corrections nécessaires stp. À date, c'est un total de {total}h:

{résumé}'''
    message = message.format(résumé=str(résumé), **stats)

    html = '''<p>Salut Émile, voici les heures que tu as rentrées cette semaine à date, n'oublie pas d'effectuer les corrections nécessaires stp. À date, c'est un total de {total}h pour {décalage}:</p>

{résumé}

<p>Par jour, ça fait:</p>

{quotidien}'''
    html = html.format(résumé=résumé.to_html(),
                       quotidien=quotidien.to_html(),
                       décalage=décalage,
                       **stats)
    courriel = Courriel(destinataire=config.get('courriel', 'destinataire'),
                        expéditeur=config.get('courriel', 'expéditeur'),
                        objet='Heures à date cette semaine',
                        contenu=message,
                        html=html)
    courriel.envoyer(adresse=config.get('courriel', 'smtp'))


if __name__ == '__main__':
    main()
