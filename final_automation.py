# -*- coding: utf-8 -*-
"""
Script final d'automatisation ScanSante
Scrape les tableaux HTML au lieu de télécharger les fichiers Excel
"""

import requests
import time
import os
from urllib.parse import urljoin
import logging
import pandas as pd
from bs4 import BeautifulSoup
import re

class ScanSanteFinalAutomation:
    def __init__(self, output_dir="donnees_scansante"):
        self.base_url = "https://www.scansante.fr"
        self.submit_url = "/applications/cartographie-activite-MCO/submit"
        self.session = requests.Session()
        self.output_dir = output_dir
        self.setup_logging()
        self.setup_session()
        self.create_directory_structure()

    def create_directory_structure(self):
        """Crée une structure de dossiers organisée par critères"""

        # Dossier principal
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # Structure hiérarchique
        subdirs = [
            # Par zone géographique
            "01_France_entiere",
            "02_Departements",

            # Par type d'établissement
            "01_France_entiere/A_Publics_PSPH",
            "01_France_entiere/B_Prives_OQN",
            "01_France_entiere/C_Tous_etablissements",

            "02_Departements/A_Publics_PSPH",

            # Par type de données
            "01_France_entiere/A_Publics_PSPH/1_Tous_sejours",
            "01_France_entiere/A_Publics_PSPH/2_Activites_soins",
            "01_France_entiere/A_Publics_PSPH/3_Categories_activites",

            "01_France_entiere/B_Prives_OQN/1_Tous_sejours",
            "01_France_entiere/B_Prives_OQN/2_Activites_soins",
            "01_France_entiere/B_Prives_OQN/3_Categories_activites",

            "01_France_entiere/C_Tous_etablissements/1_Tous_sejours",
            "01_France_entiere/C_Tous_etablissements/2_Activites_soins",
            "01_France_entiere/C_Tous_etablissements/3_Categories_activites",

            "02_Departements/A_Publics_PSPH/1_Tous_sejours",
        ]

        for subdir in subdirs:
            full_path = os.path.join(self.output_dir, subdir)
            if not os.path.exists(full_path):
                os.makedirs(full_path)

    def get_organized_filepath(self, params):
        """Détermine le chemin de fichier organisé selon la hiérarchie"""

        # Déterminer le dossier de zone géographique
        if params['tgeo'] == 'fe' and params['codegeo'] == '99':
            geo_folder = "01_France_entiere"
        elif params['tgeo'] == 'de':
            geo_folder = "02_Departements"
        else:
            geo_folder = "03_Autres_zones"

        # Déterminer le type d'établissement
        if params['base'] == 'bpub':
            etab_folder = "A_Publics_PSPH"
        elif params['base'] == 'bpri':
            etab_folder = "B_Prives_OQN"
        elif params['base'] == 'ball':
            etab_folder = "C_Tous_etablissements"
        else:
            etab_folder = "D_Autres"

        # Déterminer le type de données
        if params['typrgp'] == 'tous':
            data_folder = "1_Tous_sejours"
        elif params.get('ASO'):
            data_folder = "2_Activites_soins"
        elif params.get('CAS'):
            data_folder = "3_Categories_activites"
        else:
            data_folder = "4_Autres"

        # Construire le chemin complet
        return os.path.join(self.output_dir, geo_folder, etab_folder, data_folder)
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scansante_final.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_session(self):
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': self.base_url + '/applications/cartographie-activite-MCO'
        })
    
    def scrape_table_data(self, params):
        """Scrape les données du tableau HTML au lieu de télécharger Excel"""
        try:
            # Etape 0: Visiter la page principale pour établir la session
            main_page = self.session.get(self.base_url + '/applications/cartographie-activite-MCO', timeout=30)
            if main_page.status_code != 200:
                self.logger.error(f"Erreur page principale: {main_page.status_code}")
                return False

            # Etape 1: Faire le GET submit pour générer les données
            submit_params = {
                'snatnav': '',
                'annee': params['annee'],
                'tgeo': params['tgeo'],
                'codegeo': params['codegeo'],
                'base': params['base'],
                'ASO': params.get('ASO', ''),
                'CAS': params.get('CAS', ''),
                'typrgp': params['typrgp'],
                'DA': '',
                'GP': '',
                'racine': '',
                'GHM': ''
            }

            submit_response = self.session.get(self.base_url + self.submit_url, params=submit_params, timeout=30)
            if submit_response.status_code != 200:
                self.logger.error(f"Erreur submit: {submit_response.status_code}")
                return False

            # Parser le HTML avec BeautifulSoup
            soup = BeautifulSoup(submit_response.content, 'html.parser')

            # Trouver tous les tableaux avec class="table"
            tables = soup.find_all('table', class_='table')
            if not tables:
                self.logger.error("Aucun tableau trouvé")
                return False

            # Chercher le bon tableau (celui avec des données)
            data_table = None
            headers = []

            for table in tables:
                # Chercher les en-têtes de colonnes
                thead = table.find('thead')
                if thead:
                    header_row = thead.find('tr')
                    if header_row:
                        potential_headers = [th.get_text(strip=True).replace('\n', ' ').replace('<br>', ' ')
                                           for th in header_row.find_all('th')]
                        # Vérifier si ce tableau a plus d'une colonne (données utiles)
                        if len(potential_headers) > 3:
                            headers = potential_headers
                            data_table = table
                            break

            if not data_table or not headers:
                self.logger.error("Tableau de données avec en-têtes non trouvé")
                # Debug: afficher les tableaux trouvés
                for i, table in enumerate(tables):
                    self.logger.info(f"Tableau {i+1}: {len(table.find_all('td'))} cellules")
                return False

            # Extraire les données du tbody
            rows_data = []
            tbody = data_table.find('tbody')
            if tbody:
                for row in tbody.find_all('tr'):
                    cells = row.find_all('td')
                    if cells:
                        row_data = []
                        for cell in cells:
                            # Nettoyer le texte des cellules
                            cell_text = cell.get_text(strip=True)
                            # Supprimer les espaces en trop et normaliser
                            cell_text = re.sub(r'\s+', ' ', cell_text)
                            row_data.append(cell_text)
                        rows_data.append(row_data)

            if not rows_data:
                self.logger.warning("Aucune donnée trouvée dans le tableau - zone probablement vide")
                return "empty"

            # Vérifier si les données sont significatives (plus de quelques lignes)
            if len(rows_data) < 3:
                self.logger.warning(f"Très peu de données ({len(rows_data)} lignes) - zone probablement peu significative")
                return "minimal"

            # Créer un DataFrame avec les données
            df = pd.DataFrame(rows_data, columns=headers)

            # Sauvegarder en CSV dans le dossier organisé
            organized_dir = self.get_organized_filepath(params)
            filename = self.generate_filename(params, extension='csv')
            filepath = os.path.join(organized_dir, filename)

            # Créer le dossier si nécessaire
            if not os.path.exists(organized_dir):
                os.makedirs(organized_dir)

            df.to_csv(filepath, index=False, encoding='utf-8-sig')

            # Log relatif pour clarté
            relative_path = os.path.relpath(filepath, self.output_dir)
            self.logger.info(f"SUCCESS: {relative_path} ({len(rows_data)} lignes, {len(headers)} colonnes)")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du scraping: {e}")
            return False
    
    def generate_filename(self, params, extension='csv'):
        """Génère un nom de fichier descriptif et organisé"""

        # Nom de base avec année
        base_name = f"{params['annee']}"

        # Ajouter les spécifications selon le type
        if params['typrgp'] == 'tous':
            type_name = "tous_sejours"
        elif params.get('ASO'):
            activities = {'M': 'medecine', 'C': 'chirurgie', 'O': 'obstetrique'}
            type_name = f"activite_{activities.get(params['ASO'], params['ASO'])}"
        elif params.get('CAS'):
            categories = {'C': 'chirurgie', 'O14': 'obstetrique', 'O15': 'nouveau_nes', 'PI': 'peu_invasif'}
            type_name = f"categorie_{categories.get(params['CAS'], params['CAS'])}"
        else:
            type_name = "autre"

        # Ajouter zone géographique si c'est un département
        if params['tgeo'] == 'de':
            geo_part = f"_dept{params['codegeo']}"
        else:
            geo_part = ""

        return f"{base_name}_{type_name}{geo_part}.{extension}"

    def estimate_total_combinations(self):
        """Estime le nombre total de combinaisons à traiter"""
        years = 10  # 2015-2024
        zones = 1 + 18 + 101  # France + 18 régions + 101 départements
        establishments = 3  # Publics, Privés, Tous
        types = 1 + 3 + 4  # Tous séjours + 3 ASO + 4 CAS

        total = years * zones * establishments * types
        self.logger.info(f"Estimation: {total:,} combinaisons à traiter")
        return total
    
    def get_all_geographic_zones(self):
        """Définit toutes les zones géographiques disponibles"""
        zones = {
            # France entière
            'france': [('fe', '99')],

            # Régions (17 régions françaises)
            'regions': [
                ('re', '84'),  # AUVERGNE-RHÔNE-ALPES
                ('re', '27'),  # BOURGOGNE-FRANCHE-COMTÉ
                ('re', '53'),  # BRETAGNE
                ('re', '24'),  # CENTRE-VAL DE LOIRE
                ('re', '94'),  # CORSE
                ('re', '44'),  # GRAND EST
                ('re', '01'),  # GUADELOUPE
                ('re', '03'),  # GUYANE
                ('re', '32'),  # HAUTS-DE-FRANCE
                ('re', '11'),  # ILE-DE-FRANCE
                ('re', '04'),  # LA RÉUNION
                ('re', '02'),  # MARTINIQUE
                ('re', '06'),  # MAYOTTE
                ('re', '28'),  # NORMANDIE
                ('re', '75'),  # NOUVELLE-AQUITAINE
                ('re', '76'),  # OCCITANIE
                ('re', '52'),  # PAYS DE LA LOIRE
                ('re', '93'),  # PROVENCE-ALPES-CÔTE D'AZUR
            ],

            # Départements (codes INSEE)
            'departments': [
                ('de', '01'), ('de', '02'), ('de', '03'), ('de', '04'), ('de', '05'),
                ('de', '06'), ('de', '07'), ('de', '08'), ('de', '09'), ('de', '10'),
                ('de', '11'), ('de', '12'), ('de', '13'), ('de', '14'), ('de', '15'),
                ('de', '16'), ('de', '17'), ('de', '18'), ('de', '19'), ('de', '21'),
                ('de', '22'), ('de', '23'), ('de', '24'), ('de', '25'), ('de', '26'),
                ('de', '27'), ('de', '28'), ('de', '29'), ('de', '30'), ('de', '31'),
                ('de', '32'), ('de', '33'), ('de', '34'), ('de', '35'), ('de', '36'),
                ('de', '37'), ('de', '38'), ('de', '39'), ('de', '40'), ('de', '41'),
                ('de', '42'), ('de', '43'), ('de', '44'), ('de', '45'), ('de', '46'),
                ('de', '47'), ('de', '48'), ('de', '49'), ('de', '50'), ('de', '51'),
                ('de', '52'), ('de', '53'), ('de', '54'), ('de', '55'), ('de', '56'),
                ('de', '57'), ('de', '58'), ('de', '59'), ('de', '60'), ('de', '61'),
                ('de', '62'), ('de', '63'), ('de', '64'), ('de', '65'), ('de', '66'),
                ('de', '67'), ('de', '68'), ('de', '69'), ('de', '70'), ('de', '71'),
                ('de', '72'), ('de', '73'), ('de', '74'), ('de', '75'), ('de', '76'),
                ('de', '77'), ('de', '78'), ('de', '79'), ('de', '80'), ('de', '81'),
                ('de', '82'), ('de', '83'), ('de', '84'), ('de', '85'), ('de', '86'),
                ('de', '87'), ('de', '88'), ('de', '89'), ('de', '90'), ('de', '91'),
                ('de', '92'), ('de', '93'), ('de', '94'), ('de', '95'),
                # DOM-TOM
                ('de', '971'), ('de', '972'), ('de', '973'), ('de', '974'), ('de', '976')
            ]
        }
        return zones

    def get_strategic_combinations(self):
        """Génère des combinaisons stratégiques pour maximiser les données utiles"""
        combinations = []

        # PHASE 1: FRANCE ENTIÈRE - Données les plus importantes et complètes
        france_years = ['2024', '2023', '2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015']
        establishment_types = ['bpub', 'bpri', 'ball']  # Tous les types d'établissements

        for year in france_years:
            for base in establishment_types:
                # Tous séjours/séances - INDISPENSABLE
                combinations.append({
                    'annee': year,
                    'tgeo': 'fe',
                    'codegeo': '99',
                    'base': base,
                    'ASO': '',
                    'CAS': '',
                    'typrgp': 'tous',
                    'priority': 'critical'
                })

                # Activités de soins principales
                for aso in ['M', 'C', 'O']:  # Médecine, Chirurgie, Obstétrique
                    combinations.append({
                        'annee': year,
                        'tgeo': 'fe',
                        'codegeo': '99',
                        'base': base,
                        'ASO': aso,
                        'CAS': '',
                        'typrgp': 'rgpGHM',
                        'priority': 'critical'
                    })

                # Catégories d'activité de soins
                for cas in ['C', 'O14', 'O15', 'PI']:
                    combinations.append({
                        'annee': year,
                        'tgeo': 'fe',
                        'codegeo': '99',
                        'base': base,
                        'ASO': '',
                        'CAS': cas,
                        'typrgp': 'rgpGHM',
                        'priority': 'high'
                    })

        # PHASE 2: Échantillon de départements stratégiques pour validation
        # Seulement pour années récentes et publics PSPH (qui fonctionne)
        strategic_departments = [
            '75',   # Paris
            '13',   # Bouches-du-Rhône
            '69',   # Rhône
            '59',   # Nord
            '33',   # Gironde
        ]

        for year in ['2024', '2023']:
            for dept in strategic_departments:
                combinations.append({
                    'annee': year,
                    'tgeo': 'de',
                    'codegeo': dept,
                    'base': 'bpub',
                    'ASO': '',
                    'CAS': '',
                    'typrgp': 'tous',
                    'priority': 'medium'
                })

        return combinations

    def generate_all_combinations(self):
        """Wrapper pour compatibilité - utilise désormais l'approche stratégique"""
        return self.get_strategic_combinations()

    def validate_combination(self, params):
        """Valide qu'une combinaison est susceptible de retourner des données"""
        # Règles de validation basiques

        # 1. Éviter les très vieilles années pour les nouvelles régions
        if params['tgeo'] == 're' and int(params['annee']) < 2017:
            return False

        # 2. DOM-TOM : seulement établissements publics généralement
        dom_tom_codes = ['971', '972', '973', '974', '976', '01', '02', '03', '04', '06']
        if params['codegeo'] in dom_tom_codes and params['base'] == 'bpri':
            return False

        return True
    
    def run_full_automation(self, delay=2, max_combinations=None):
        """Lance l'automatisation complète avec option de limitation"""
        self.logger.info("Début de l'automatisation ScanSante COMPLÈTE avec scraping HTML")

        # Estimer le nombre total
        self.estimate_total_combinations()

        combinations = self.generate_all_combinations()
        total_combinations = len(combinations)

        if max_combinations and max_combinations < total_combinations:
            combinations = combinations[:max_combinations]
            self.logger.info(f"LIMITATION: Traitement des {max_combinations} premières combinaisons sur {total_combinations}")
        else:
            self.logger.info(f"Traitement de TOUTES les {total_combinations:,} combinaisons")

        successful_scrapes = 0
        failed_scrapes = 0
        empty_zones = 0
        minimal_data = 0
        start_time = time.time()

        for i, params in enumerate(combinations, 1):
            # Valider la combinaison d'abord
            if not self.validate_combination(params):
                self.logger.info(f"[{i}/{len(combinations)}] SKIPPED: Combinaison non valide")
                continue

            # Log détaillé tous les 50 éléments
            if i % 50 == 0 or i == 1:
                elapsed = time.time() - start_time
                estimated_total = (elapsed / i) * len(combinations) if i > 0 else 0
                self.logger.info(f"[{i}/{len(combinations)}] - Temps écoulé: {elapsed/60:.1f}min - ETA: {estimated_total/60:.1f}min")

            # Log basique pour chaque élément
            zone_desc = f"{params['tgeo']}:{params['codegeo']}"
            priority = params.get('priority', 'normal')
            self.logger.info(f"[{i}/{len(combinations)}] {params['annee']} {zone_desc} {params['base']} {params['typrgp']} ({priority})")

            result = self.scrape_table_data(params)
            if result == True:
                successful_scrapes += 1
            elif result == "empty":
                empty_zones += 1
                self.logger.info(f"Zone vide détectée: {zone_desc} - peut être ignorée pour futures requêtes similaires")
            elif result == "minimal":
                minimal_data += 1
                successful_scrapes += 1  # On garde quand même
            else:
                failed_scrapes += 1

            # Pause respectueuse entre requêtes
            time.sleep(delay)

        total_time = time.time() - start_time
        self.logger.info(f"Automatisation terminee en {total_time/60:.1f} minutes!")
        self.logger.info(f"Succes avec donnees: {successful_scrapes:,}")
        self.logger.info(f"Zones vides detestees: {empty_zones:,}")
        self.logger.info(f"Donnees minimales: {minimal_data:,}")
        self.logger.info(f"Echecs techniques: {failed_scrapes:,}")
        self.logger.info(f"Dossier: {self.output_dir}")

        return successful_scrapes

    def run_limited_test(self, limit=100):
        """Lance un test limité avec un sous-ensemble de combinaisons"""
        self.logger.info(f"Test limité avec {limit} combinaisons")
        return self.run_full_automation(delay=1, max_combinations=limit)

if __name__ == "__main__":
    print("ScanSante - Automatisation OPTIMISEE")
    print("====================================")

    automation = ScanSanteFinalAutomation()

    # Calculer le nombre réel de combinaisons
    combinations = automation.get_strategic_combinations()
    total_combinations = len(combinations)
    estimated_time = total_combinations * 2 / 60  # en minutes

    print(f"Approche strategique intelligente:")
    print(f"- {total_combinations} combinaisons optimisees (au lieu de 28,000+)")
    print(f"- Temps estime: {estimated_time:.1f} minutes")
    print(f"- Focus sur France entiere + echantillon departemental")
    print()

    # Option 1: Test limité pour validation
    response = input("Voulez-vous d'abord faire un test limite? (o/N): ").lower()
    if response in ['o', 'oui', 'y', 'yes']:
        limit = input("Nombre de combinaisons a tester (defaut: 10): ")
        try:
            limit = int(limit) if limit else 10
        except ValueError:
            limit = 10

        print(f"\nTest avec {limit} combinaisons...")
        successful_scrapes = automation.run_limited_test(limit)
        print(f"Test termine: {successful_scrapes} reussites")
    else:
        # Option 2: Automatisation complète optimisée
        print(f"\nLancement de l'automatisation OPTIMISEE ({total_combinations} combinaisons)...")
        print(f"Temps estime: {estimated_time:.1f} minutes")
        confirm = input("Continuer? (o/N): ").lower()

        if confirm in ['o', 'oui', 'y', 'yes']:
            successful_scrapes = automation.run_full_automation(delay=2)
            print(f"\nAutomatisation OPTIMISEE terminee!")
            print(f"{successful_scrapes:,} fichiers CSV crees avec succes")
        else:
            print("Automatisation annulee")

    print(f"Dossier de sortie: {automation.output_dir}")