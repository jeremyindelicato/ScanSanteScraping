# -*- coding: utf-8 -*-
"""
Script final d'automatisation ScanSante
FONCTIONNE! Telecharge automatiquement tous les fichiers Excel
"""

import requests
import time
import os
from urllib.parse import urljoin
import logging

class ScanSanteFinalAutomation:
    def __init__(self, output_dir="excel_files"):
        self.base_url = "https://www.scansante.fr"
        self.submit_url = "/applications/cartographie-activite-MCO/submit" 
        self.excel_url = "/applications/cartographie-activite-MCO/outilExcel"
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
    
    def download_excel_file(self, params):
        """Telecharge un fichier Excel avec etablissement de session complet"""

        try:
            # Etape 0: Visiter la page principale pour etablir la session
            main_page = self.session.get(self.base_url + '/applications/cartographie-activite-MCO', timeout=30)
            if main_page.status_code != 200:
                self.logger.error(f"Erreur page principale: {main_page.status_code}")
                return False

            # Etape 1: Faire le GET submit pour generer les donnees
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

            # Etape 2: POST Excel avec EXACTEMENT les memes parametres que le GET
            excel_data = {
                'snatnav': '',
                'annee': params['annee'],
                'tgeo': params['tgeo'],
                'codegeo': params['codegeo'],
                'base': params['base'],
                'ASO': params.get('ASO', ''),  # CORRECTION: ASO au lieu de A50
                'CAS': params.get('CAS', ''),
                'typrgp': params['typrgp'],
                'DA': '',
                'GP': '',
                'racine': '',
                'GHM': ''
            }

            # Headers specifiques pour simuler le formulaire
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/vnd.ms-excel,*/*;q=0.8',
                'Referer': self.base_url + '/applications/cartographie-activite-MCO',
                'Origin': self.base_url,
                'Cache-Control': 'no-cache'
            }

            response2 = self.session.post(
                self.base_url + self.excel_url,
                data=excel_data,
                headers=headers,
                timeout=30
            )

            if response2.status_code != 200:
                self.logger.error(f"Erreur etape 2: Status {response2.status_code}")
                return False

            # DEBUG: Verifier ce qu'on recoit
            self.logger.info(f"Content-Type recu: {response2.headers.get('Content-Type', 'Non defini')}")
            self.logger.info(f"Taille contenu: {len(response2.content)} bytes")

            # Si c'est du HTML, sauvegarder pour debug
            if response2.content.startswith(b'<!doctype html>') or response2.content.startswith(b'<html'):
                debug_file = f"debug_response_{params['annee']}_{params.get('ASO', 'tous')}.html"
                with open(debug_file, 'wb') as f:
                    f.write(response2.content)
                self.logger.error(f"Recu HTML au lieu d'Excel! Sauvegarde: {debug_file}")
                return False

            # Verifier si c'est un fichier Excel valide
            if len(response2.content) > 1000:  # Taille minimum raisonnable
                # Verifier les magic bytes Excel
                # .xls (ancien format) commence par: D0 CF 11 E0 A1 B1 1A E1
                # .xlsx (nouveau format) commence par: PK
                is_excel = (response2.content[:2] == b'PK' or
                           response2.content[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')

                if is_excel:
                    filename = self.generate_filename(params)
                    filepath = os.path.join(self.output_dir, filename)

                    with open(filepath, 'wb') as f:
                        f.write(response2.content)

                    self.logger.info(f"SUCCESS: {filename} ({len(response2.content)} bytes)")
                    return True
                else:
                    self.logger.error(f"Le contenu n'est pas un fichier Excel valide. Premieres bytes: {response2.content[:20]}")
                    return False
            else:
                self.logger.warning(f"Fichier trop petit: {len(response2.content)} bytes")
                if len(response2.content) < 500:
                    self.logger.warning(f"Contenu: {response2.content[:200]}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur: {e}")
            return False
    
    def generate_filename(self, params):
        """Genere un nom de fichier descriptif"""
        aso_part = f"_ASO{params['ASO']}" if params.get('ASO') else ""
        cas_part = f"_CAS{params['CAS']}" if params.get('CAS') else ""
        return f"scan_{params['annee']}_{params['tgeo']}_{params['codegeo']}_{params['typrgp']}{aso_part}{cas_part}.xls"
    
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
        """Lance l'automatisation complete"""
        self.logger.info("Debut de l'automatisation ScanSante FINALE")
        
        combinations = self.generate_all_combinations()
        self.logger.info(f"Nombre total de combinaisons: {len(combinations)}")
        
        successful_downloads = 0
        failed_downloads = 0
        
        for i, params in enumerate(combinations, 1):
            self.logger.info(f"[{i}/{len(combinations)}] {params['annee']} - {params['typrgp']}")
            
            if self.download_excel_file(params):
                successful_downloads += 1
            else:
                failed_downloads += 1
            
            # Pause respectueuse entre telechargements
            time.sleep(delay)
        
        self.logger.info(f"Automatisation terminee!")
        self.logger.info(f"Succes: {successful_downloads}")
        self.logger.info(f"Echecs: {failed_downloads}")
        self.logger.info(f"Dossier: {self.output_dir}")
        
        return successful_downloads

if __name__ == "__main__":
    print("ScanSante - Test Debug")
    print("=====================")

    automation = ScanSanteFinalAutomation()

    # Test avec une seule combinaison pour debug
    test_params = {
        'annee': '2024',
        'tgeo': 'fe',
        'codegeo': '99',
        'base': 'bpub',
        'ASO': 'M',
        'CAS': 'C',
        'typrgp': 'rgpGHM'
    }

    print(f"Test avec: {test_params}")
    success = automation.download_excel_file(test_params)
    print(f"Resultat: {'SUCCESS' if success else 'ECHEC'}")

    # Si echec, examiner le fichier debug genere
    if not success:
        print("Vérifiez le fichier debug_response_*.html pour voir l'erreur")