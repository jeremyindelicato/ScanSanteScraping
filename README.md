# ScanSante Data Automation

**Extraction automatisée et intelligente des données MCO** depuis https://www.scansante.fr/applications/cartographie-activite-MCO

## 🎯 Objectif

Automatiser l'extraction complète des données d'activité MCO (Médecine, Chirurgie, Obstétrique) des établissements de santé français avec une approche optimisée pour maximiser la qualité des données tout en minimisant les requêtes inutiles.

## 🚀 Fonctionnalités principales

### ✅ Scraping HTML intelligent
- **Abandon du téléchargement Excel** (problématique)
- **Parsing direct des tableaux HTML** avec BeautifulSoup
- **Export automatique en CSV** structuré

### ✅ Approche stratégique optimisée
- **250 combinaisons** au lieu de 28,000+ possibles
- **Focus sur la France entière** (données les plus complètes)
- **Échantillonnage départemental** pour validation
- **Filtrage automatique** des combinaisons vides

### ✅ Organisation hiérarchique des données
```
donnees_scansante/
├── 01_France_entiere/
│   ├── A_Publics_PSPH/
│   │   ├── 1_Tous_sejours/        # Données globales
│   │   ├── 2_Activites_soins/     # Médecine, Chirurgie, Obstétrique
│   │   └── 3_Categories_activites/ # Classifications CAS
│   ├── B_Prives_OQN/
│   └── C_Tous_etablissements/
└── 02_Departements/
    └── A_Publics_PSPH/
```

## 📊 Couverture des données

### **Temporelle**
- **10 années** : 2015-2024 (France entière)
- **2 années** : 2023-2024 (échantillon départemental)

### **Géographique**
- **France entière** (priorité maximale)
- **5 départements stratégiques** : Paris, Bouches-du-Rhône, Rhône, Nord, Gironde

### **Types d'établissements**
- **Publics PSPH** (Publics et Participants au Service Public Hospitalier)
- **Privés OQN** (Objectifs Quantifiés Nationaux)
- **Tous établissements** (agrégation)

### **Types de données**
- **Tous séjours/séances** (données globales)
- **Activités de soins** : Médecine (M), Chirurgie (C), Obstétrique (O)
- **Catégories d'activité** : Chirurgie (C), Obstétrique (O14), Nouveau-nés (O15), Peu Invasif (PI)

## 🛠️ Installation et utilisation

### Prérequis
```bash
pip install requests pandas beautifulsoup4 lxml
```

### Lancement
```bash
python final_automation.py
```

### Options disponibles
1. **Test limité** : Valider le fonctionnement avec un échantillon
2. **Automatisation complète** : Extraire les 250 combinaisons (~8 minutes)

## 📋 Structure des données extraites

### **12 colonnes par fichier CSV :**
1. **Catégorie** - Type d'établissement (CH, CHU, etc.)
2. **Finess** - Identifiant unique établissement
3. **Raison Sociale** - Nom de l'établissement
4. **Période** - Période de référence (M12 = 12 mois)
5. **Nombre de séjours/séances total**
6. **Nombre de séjours en hospitalisation complète**
7. **Nombre de séjours en hospitalisation partielle**
8. **Nombre de séances**
9. **Sexe ratio (% hommes)**
10. **Âge moyen**
11. **Durée moyenne de séjour**
12. **% décès**

### **Nomenclature des fichiers :**
- `YYYY_tous_sejours.csv` - Données globales
- `YYYY_activite_medecine.csv` - Activité médecine
- `YYYY_categorie_chirurgie.csv` - Catégorie chirurgie
- `YYYY_tous_sejours_dept75.csv` - Données départementales

## ⚡ Performances

- **Temps d'exécution** : ~8 minutes pour 250 combinaisons
- **Taille des données** : ~750-780 lignes par fichier France entière
- **Taux de succès** : 100% pour les combinaisons validées
- **Pause respectueuse** : 2 secondes entre requêtes

## 🔧 Architecture technique

### **Workflow de traitement**
1. **Session HTTP** avec headers réalistes
2. **Requête GET** `/submit` avec paramètres de filtrage
3. **Parsing HTML** du tableau principal
4. **Validation et nettoyage** des données
5. **Export CSV** dans l'arborescence organisée

### **Gestion des erreurs**
- **Détection automatique** des zones vides
- **Validation des combinaisons** avant traitement
- **Logging détaillé** pour traçabilité
- **Reprise possible** en cas d'interruption

### **Optimisations**
- **Approche stratégique** évitant 27,000+ requêtes inutiles
- **Cache de session** pour performance
- **Structures de données** optimisées

## 📁 Fichiers du projet

- `final_automation.py` - Script principal optimisé
- `CLAUDE.md` - Documentation technique complète
- `Aborescence des filtres.md` - Cartographie exhaustive des filtres disponibles
- `requirements.txt` - Dépendances Python
- `scansante_final.log` - Logs d'exécution
- `donnees_scansante/` - Dossier de sortie avec structure hiérarchique

## 🎯 Résultats attendus

**~250 fichiers CSV** parfaitement organisés contenant l'intégralité des données MCO françaises pour analyse, recherche ou business intelligence.

**Couverture maximale** avec approche intelligente : toutes les données importantes sans surcharge inutile.