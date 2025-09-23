#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage des données ScrapingScanSante
Traite tous les fichiers CSV avec la structure standard
"""

import pandas as pd
import os
import glob
import logging
from pathlib import Path

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_cleaning.log'),
        logging.StreamHandler()
    ]
)

def clean_csv_file(input_file, output_file):
    """
    Nettoie un fichier CSV selon les règles définies:
    1. Supprime la dernière ligne (total)
    2. Convert Finess en texte
    3. Remplace "1 à 10" par "5" et convertit en entier
    """
    try:
        # Lecture du fichier
        df = pd.read_csv(input_file)
        logging.info(f"Traitement de {input_file} - {len(df)} lignes")

        # 1. Supprimer la dernière ligne (total)
        df = df.iloc[:-1]
        logging.info(f"Dernière ligne supprimée - {len(df)} lignes restantes")

        # 2. Finess en texte (avec zéros de tête préservés)
        if 'Finess' in df.columns:
            df['Finess'] = df['Finess'].astype(str)
            # Assurer 9 chiffres pour Finess (format standard)
            df['Finess'] = df['Finess'].str.zfill(9)
            logging.info("Colonne Finess convertie en texte")

        # 3. Remplacer "1 à 10" par "5" dans toutes les colonnes numériques
        columns_to_convert = [
            'Nombre de séjours/séances total',
            'Nombre de séjours en hospit complète',
            'Nombre de séjours en hospit partielle',
            'Nombre de séances'
        ]

        replacements_made = 0
        for col in columns_to_convert:
            if col in df.columns:
                # Remplacer "1 à 10" par "5"
                mask = df[col] == "1 à 10"
                replacements_made += mask.sum()
                df.loc[mask, col] = "5"

                # Convertir en entier (gérer les NaN)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        logging.info(f"{replacements_made} valeurs '1 à 10' remplacées par '5'")

        # Sauvegarde
        df.to_csv(output_file, index=False)
        logging.info(f"Fichier nettoyé sauvegardé: {output_file}")

        return True, len(df)

    except Exception as e:
        logging.error(f"Erreur lors du traitement de {input_file}: {str(e)}")
        return False, 0

def clean_all_csv_files(input_dir="csv_files", output_dir="csv_files_cleaned"):
    """
    Nettoie tous les fichiers CSV du dossier d'entrée
    """
    # Créer le dossier de sortie
    Path(output_dir).mkdir(exist_ok=True)

    # Trouver tous les fichiers CSV
    csv_pattern = os.path.join(input_dir, "*.csv")
    csv_files = glob.glob(csv_pattern)

    if not csv_files:
        logging.warning(f"Aucun fichier CSV trouvé dans {input_dir}")
        return

    logging.info(f"Trouvé {len(csv_files)} fichiers CSV à traiter")

    success_count = 0
    total_rows = 0

    for csv_file in csv_files:
        # Nom du fichier de sortie
        filename = os.path.basename(csv_file)
        output_file = os.path.join(output_dir, f"cleaned_{filename}")

        # Nettoyage
        success, rows = clean_csv_file(csv_file, output_file)
        if success:
            success_count += 1
            total_rows += rows

    logging.info(f"=== RÉSUMÉ ===")
    logging.info(f"Fichiers traités avec succès: {success_count}/{len(csv_files)}")
    logging.info(f"Total lignes nettoyées: {total_rows}")
    logging.info(f"Fichiers sauvegardés dans: {output_dir}")

def create_consolidated_file(input_dir="csv_files_cleaned", output_file="scansante_master_cleaned.csv"):
    """
    Consolide tous les fichiers nettoyés en un seul fichier pour Power BI
    """
    try:
        csv_pattern = os.path.join(input_dir, "cleaned_*.csv")
        csv_files = glob.glob(csv_pattern)

        if not csv_files:
            logging.warning(f"Aucun fichier nettoyé trouvé dans {input_dir}")
            return

        all_dataframes = []
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            # Ajouter une colonne source pour traçabilité
            df['Fichier_Source'] = os.path.basename(csv_file)
            all_dataframes.append(df)

        # Consolidation
        master_df = pd.concat(all_dataframes, ignore_index=True)
        master_df.to_csv(output_file, index=False)

        logging.info(f"Fichier consolidé créé: {output_file}")
        logging.info(f"Total lignes consolidées: {len(master_df)}")

    except Exception as e:
        logging.error(f"Erreur lors de la consolidation: {str(e)}")

if __name__ == "__main__":
    logging.info("=== DÉBUT DU NETTOYAGE DES DONNÉES ===")

    # Nettoyage des fichiers individuels
    clean_all_csv_files()

    # Création du fichier consolidé
    create_consolidated_file()

    logging.info("=== NETTOYAGE TERMINÉ ===")