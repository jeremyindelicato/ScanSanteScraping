#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Flask pour ScrapingScanSante
Interface web simple pour lancer et suivre la collecte de données
"""

from flask import Flask, render_template, jsonify, send_file
import threading
import time
import os
import glob
from datetime import datetime
import queue
import logging

# Import du script d'automation existant (sans le modifier)
from final_automation import ScanSanteFinalAutomation

app = Flask(__name__)

# État global de l'application
app_state = {
    'is_running': False,
    'progress': 0,
    'current_file': '',
    'total_files': 0,
    'successful': 0,
    'failed': 0,
    'start_time': None,
    'end_time': None,
    'logs': []
}

# Queue pour les logs en temps réel
log_queue = queue.Queue()

class WebLogger(logging.Handler):
    """Handler personnalisé pour capturer les logs et les envoyer au frontend"""
    def emit(self, record):
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': record.getMessage()
        }
        app_state['logs'].append(log_entry)
        # Garder seulement les 100 derniers logs
        if len(app_state['logs']) > 100:
            app_state['logs'] = app_state['logs'][-100:]

def run_automation_thread():
    """Lance l'automation dans un thread séparé"""
    try:
        app_state['is_running'] = True
        app_state['start_time'] = datetime.now()
        app_state['progress'] = 0
        app_state['logs'] = []

        # Créer l'instance d'automation
        automation = ScanSanteFinalAutomation()

        # Ajouter notre handler personnalisé au logger
        web_handler = WebLogger()
        automation.logger.addHandler(web_handler)

        # Obtenir le nombre total de combinaisons
        combinations = automation.get_strategic_combinations()
        app_state['total_files'] = len(combinations)

        # Wrapper de la méthode scrape_table_data pour tracker la progression
        original_scrape = automation.scrape_table_data

        def tracked_scrape(params):
            app_state['current_file'] = f"{params['annee']}_{params['typrgp']}_{params['base']}"
            result = original_scrape(params)

            if result == True:
                app_state['successful'] += 1
            else:
                app_state['failed'] += 1

            # Mise à jour de la progression
            total_processed = app_state['successful'] + app_state['failed']
            app_state['progress'] = int((total_processed / app_state['total_files']) * 100)

            return result

        # Remplacer temporairement la méthode
        automation.scrape_table_data = tracked_scrape

        # Lancer l'automation
        automation.run_full_automation(delay=2)

        app_state['end_time'] = datetime.now()
        app_state['is_running'] = False
        app_state['progress'] = 100

    except Exception as e:
        app_state['is_running'] = False
        app_state['logs'].append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': 'ERROR',
            'message': f'Erreur: {str(e)}'
        })

@app.route('/')
def index():
    """Page principale"""
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_collection():
    """Démarre la collecte de données"""
    if app_state['is_running']:
        return jsonify({'error': 'Une collecte est déjà en cours'}), 400

    # Réinitialiser l'état
    app_state['successful'] = 0
    app_state['failed'] = 0
    app_state['progress'] = 0
    app_state['current_file'] = ''

    # Lancer dans un thread
    thread = threading.Thread(target=run_automation_thread)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started'})

@app.route('/api/status')
def get_status():
    """Retourne l'état actuel de la collecte"""
    elapsed_time = None
    if app_state['start_time']:
        if app_state['is_running']:
            elapsed_time = str(datetime.now() - app_state['start_time']).split('.')[0]
        elif app_state['end_time']:
            elapsed_time = str(app_state['end_time'] - app_state['start_time']).split('.')[0]

    return jsonify({
        'is_running': app_state['is_running'],
        'progress': app_state['progress'],
        'current_file': app_state['current_file'],
        'total_files': app_state['total_files'],
        'successful': app_state['successful'],
        'failed': app_state['failed'],
        'elapsed_time': elapsed_time,
        'logs': app_state['logs'][-20:]  # Derniers 20 logs
    })

@app.route('/api/download')
def download_file():
    """Télécharge le fichier consolidé"""
    master_file = 'scansante_master_cleaned.csv'
    if os.path.exists(master_file):
        return send_file(master_file, as_attachment=True)
    else:
        return jsonify({'error': 'Fichier non trouvé'}), 404

@app.route('/api/files')
def list_files():
    """Liste tous les fichiers CSV disponibles"""
    files = []

    # Fichier consolidé
    master_file = 'scansante_master_cleaned.csv'
    if os.path.exists(master_file):
        files.append({
            'name': master_file,
            'size': os.path.getsize(master_file),
            'modified': datetime.fromtimestamp(os.path.getmtime(master_file)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'consolidé'
        })

    # Fichiers nettoyés
    cleaned_files = glob.glob('donnees_scansante_cleaned/*.csv')
    for filepath in cleaned_files[:10]:  # Limiter à 10 pour l'affichage
        files.append({
            'name': os.path.basename(filepath),
            'size': os.path.getsize(filepath),
            'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S'),
            'type': 'individuel'
        })

    return jsonify({'files': files, 'total_cleaned': len(cleaned_files)})

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 ScrapingScanSante Dashboard")
    print("=" * 50)
    print("\n📍 Accédez à l'interface web sur:")
    print("   http://localhost:5000")
    print("\n⚠️  Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
