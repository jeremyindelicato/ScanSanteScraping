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
    def __init__(self, output_dir="csv_files"):
        self.base_url = "https://www.scansante.fr"
        self.submit_url = "/applications/cartographie-activite-MCO/submit"
        self.session = requests.Session()
        self.output_dir = output_dir
        self.setup_logging()
        self.setup_session()

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
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
                self.logger.error("Aucune donnée trouvée dans le tableau")
                return False

            # Créer un DataFrame avec les données
            df = pd.DataFrame(rows_data, columns=headers)

            # Sauvegarder en CSV
            filename = self.generate_filename(params, extension='csv')
            filepath = os.path.join(self.output_dir, filename)

            df.to_csv(filepath, index=False, encoding='utf-8-sig')

            self.logger.info(f"SUCCESS: {filename} ({len(rows_data)} lignes, {len(headers)} colonnes)")
            return True

        except Exception as e:
            self.logger.error(f"Erreur lors du scraping: {e}")
            return False
    
    def generate_filename(self, params, extension='csv'):
        """Génère un nom de fichier descriptif"""
        aso_part = f"_ASO{params['ASO']}" if params.get('ASO') else ""
        cas_part = f"_CAS{params['CAS']}" if params.get('CAS') else ""
        return f"scan_{params['annee']}_{params['tgeo']}_{params['codegeo']}_{params['typrgp']}{aso_part}{cas_part}.{extension}"
    
    def generate_all_combinations(self):
        """Genere toutes les combinaisons importantes avec le bon format"""
        combinations = []

        # Parametres principaux
        years = ['2024', '2023', '2022', '2021', '2020']
        geo_types = ['fe']  # France entiere
        geo_codes = ['99']  # Code France
        bases = ['bpub']

        # Nouvelles combinaisons basees sur le vrai formulaire
        activity_types = ['M', 'C', 'O']  # Medecine, Chirurgie, Obstetrique
        cas_types = ['C', 'M', 'O']       # Categories d'activite de soins

        for year in years:
            for geo in geo_types:
                for code in geo_codes:
                    for base in bases:
                        # Tous sejours/seances
                        combinations.append({
                            'annee': year,
                            'tgeo': geo,
                            'codegeo': code,
                            'base': base,
                            'ASO': '',
                            'CAS': '',
                            'typrgp': 'tous'
                        })

                        # Par activite de soins (ASO)
                        for aso in activity_types:
                            combinations.append({
                                'annee': year,
                                'tgeo': geo,
                                'codegeo': code,
                                'base': base,
                                'ASO': aso,
                                'CAS': '',
                                'typrgp': 'rgpGHM'
                            })

                        # Par categorie d'activite de soins (CAS)
                        for cas in cas_types:
                            combinations.append({
                                'annee': year,
                                'tgeo': geo,
                                'codegeo': code,
                                'base': base,
                                'ASO': '',
                                'CAS': cas,
                                'typrgp': 'rgpGHM'
                            })

        return combinations
    
    def run_full_automation(self, delay=3):
        """Lance l'automatisation complète"""
        self.logger.info("Début de l'automatisation ScanSante avec scraping HTML")

        combinations = self.generate_all_combinations()
        self.logger.info(f"Nombre total de combinaisons: {len(combinations)}")

        successful_scrapes = 0
        failed_scrapes = 0

        for i, params in enumerate(combinations, 1):
            self.logger.info(f"[{i}/{len(combinations)}] {params['annee']} - {params['typrgp']}")

            if self.scrape_table_data(params):
                successful_scrapes += 1
            else:
                failed_scrapes += 1

            # Pause respectueuse entre requêtes
            time.sleep(delay)

        self.logger.info(f"Automatisation terminée!")
        self.logger.info(f"Succès: {successful_scrapes}")
        self.logger.info(f"Échecs: {failed_scrapes}")
        self.logger.info(f"Dossier: {self.output_dir}")

        return successful_scrapes

if __name__ == "__main__":
    print("ScanSante - Automatisation complète")
    print("===================================")

    automation = ScanSanteFinalAutomation()

    # Lancer l'automatisation complète avec toutes les combinaisons
    print("Lancement de l'automatisation complète...")
    successful_scrapes = automation.run_full_automation(delay=3)

    print(f"\n🎉 Automatisation terminée!")
    print(f"📊 {successful_scrapes} fichiers CSV créés avec succès")
    print(f"📁 Dossier de sortie: {automation.output_dir}")