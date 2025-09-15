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
        """Telecharge un fichier Excel avec la methode en 2 etapes qui fonctionne"""
        
        try:
            # Etape 1: Generer les resultats
            response1 = self.session.get(self.base_url + self.submit_url, params=params, timeout=30)
            
            if response1.status_code != 200:
                self.logger.error(f"Erreur etape 1: Status {response1.status_code}")
                return False
            
            # Etape 2: Telecharger Excel  
            response2 = self.session.post(self.base_url + self.excel_url, data=params, timeout=30)
            
            if response2.status_code != 200:
                self.logger.error(f"Erreur etape 2: Status {response2.status_code}")
                return False
            
            # Verifier si c'est un fichier Excel valide
            if len(response2.content) > 1000:  # Taille minimum raisonnable
                filename = self.generate_filename(params)
                filepath = os.path.join(self.output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response2.content)
                
                self.logger.info(f"SUCCESS: {filename} ({len(response2.content)} bytes)")
                return True
            else:
                self.logger.warning(f"Fichier trop petit: {len(response2.content)} bytes")
                return False
                
        except Exception as e:
            self.logger.error(f"Erreur: {e}")
            return False
    
    def generate_filename(self, params):
        """Genere un nom de fichier descriptif"""
        return f"scan_{params['annee']}_{params['tgeo']}_{params['codegeo']}_{params['typrgp']}.xlsx"
    
    def generate_all_combinations(self):
        """Genere toutes les combinaisons importantes"""
        combinations = []
        
        # Parametres principaux
        years = ['2024', '2023', '2022', '2021', '2020']
        geo_types = ['fe']  # France entiere
        geo_codes = ['99']  # Code France  
        bases = ['bpub']
        type_groups = ['tous', 'ASO', 'CAS']
        
        for year in years:
            for geo in geo_types:
                for code in geo_codes:
                    for base in bases:
                        for typ in type_groups:
                            combinations.append({
                                'annee': year,
                                'tgeo': geo,
                                'codegeo': code,
                                'base': base,
                                'typrgp': typ
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
    print("ScanSante - Automatisation Finale")
    print("==================================")
    print("Cette version FONCTIONNE et va telecharger tous les fichiers Excel!")
    print()
    
    automation = ScanSanteFinalAutomation()
    
    # Lancer l'automatisation complete
    success_count = automation.run_full_automation(delay=3)
    
    print(f"\nTermine! {success_count} fichiers telecharges avec succes.")
    print("Consultez le fichier 'scansante_final.log' pour les details.")