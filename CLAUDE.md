# Projet ScrapingScanSante - État des lieux

## Objectif
Automatiser le téléchargement de fichiers Excel (.xls) depuis https://www.scansante.fr/applications/cartographie-activite-MCO en utilisant différentes combinaisons de filtres.

## Workflow identifié
1. **Page principale** : https://www.scansante.fr/applications/cartographie-activite-MCO
2. **Sélection filtres** → Bouton "Visualiser les résultats"
3. **Page résultats** : `/submit?params...` avec bouton Excel
4. **Clic bouton Excel** → Téléchargement fichier .xls

## Formulaire Excel analysé
```html
<form method="POST" action="outilExcel" style="display:inline;" target="_blank">
  <input type="hidden" name="snatnav" value="">
  <input type="hidden" name="annee" value="2024">
  <input type="hidden" name="tgeo" value="fe">
  <input type="hidden" name="codegeo" value="99">
  <input type="hidden" name="base" value="bpub">
  <input type="hidden" name="A50" value="M">  <!-- ATTENTION: A50 pas ASO -->
  <input type="hidden" name="CAS" value="C">
  <input type="hidden" name="typrgp" value="rgpGHM">
  <input type="hidden" name="DA" value="">
  <input type="hidden" name="GP" value="">
  <input type="hidden" name="racine" value="">
  <input type="hidden" name="GHM" value="">
</form>
```

## Problème actuel
- Le script fait correctement les requêtes GET/POST
- Mais reçoit du HTML au lieu de fichiers .xls
- Content-Type: `application/vnd.ms-excel` mais contenu = `<!doctype html>`
- Taille ~659KB mais ce sont des pages web

## Fichiers du projet
- `final_automation.py` - Script principal (corrigé plusieurs fois)
- `excel_files/` - Dossier destination (vide pour l'instant)
- `debug_response_*.html` - Fichiers debug HTML reçus à la place des .xls

## Corrections déjà effectuées
1. ✅ Workflow corrigé : GET `/submit` puis POST `/outilExcel`
2. ✅ Paramètres corrigés selon le vrai formulaire
3. ✅ Headers appropriés ajoutés
4. ✅ Magic bytes .xls configurés (D0 CF 11 E0 A1 B1 1A E1)
5. ✅ Extension .xls au lieu de .xlsx
6. ✅ Session établie correctement

## Next steps nécessaires
**Il faut analyser la vraie requête du navigateur :**
1. F12 → Network tab
2. Cliquer bouton Excel sur page résultats
3. Capturer : méthode, URL exacte, headers, paramètres
4. Vérifier tokens CSRF, cookies spéciaux

## Combinaisons à télécharger
```python
# Années: 2024, 2023, 2022, 2021, 2020
# Géographie: France entière (tgeo=fe, codegeo=99)
# Base: Publics PSPH (base=bpub)
# Types:
# - Tous séjours (typrgp=tous, ASO="", CAS="")
# - Par activité soins (typrgp=rgpGHM, ASO=M/C/O, CAS="")
# - Par catégorie soins (typrgp=rgpGHM, ASO="", CAS=M/C/O)
```

## Command pour tester
```bash
python final_automation.py
```