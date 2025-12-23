# 🤖 Configuration de la Mise à Jour Automatique

## Ce que ça fait

Le script `auto_update.py` :
- ✅ Télécharge les dernières données de tous les championnats
- ✅ Télécharge les dernières données AFCON
- ✅ Enregistre un log dans `update_log.txt`
- ✅ Tourne automatiquement chaque jour à l'heure que vous choisissez

---

## 🔧 Installation (5 minutes)

### Étape 1 : Test manuel

Double-cliquez sur `auto_update.bat` pour vérifier que ça marche.

### Étape 2 : Automatisation Windows

1. **Ouvrez le Planificateur de tâches Windows**
   - Appuyez sur `Win + R`
   - Tapez `taskschd.msc`
   - Appuyez sur Entrée

2. **Créez une nouvelle tâche**
   - Clic droit sur "Bibliothèque du Planificateur de tâches"
   - Sélectionnez "Créer une tâche de base..."

3. **Configuration**
   - **Nom** : `Mise à jour Prédicteur Football`
   - **Déclencheur** : Quotidien
   - **Heure** : `08:00` (ou l'heure que vous voulez)
   - **Action** : Démarrer un programme
   - **Programme/script** : Cliquez "Parcourir" et sélectionnez `auto_update.bat`
   - **Commencer dans** : Collez le chemin complet du dossier (exemple: `C:\Users\axelp\.gemini\antigravity\playground\axial-cosmic`)

4. **Options avancées** (Important)
   - Cochez "Exécuter même si l'utilisateur n'est pas connecté" (optionnel)
   - Cochez "Exécuter avec les autorisations maximales"

5. **Terminez**

---

## ✅ Vérification

Regardez le fichier `update_log.txt` qui se créera automatiquement.
Il contiendra l'historique de toutes les mises à jour.

Exemple :
```
[2025-12-23 08:00:15] === DEBUT MISE A JOUR AUTOMATIQUE ===
[2025-12-23 08:00:16] Telechargement des donnees des championnats...
[2025-12-23 08:00:45] Championnats: OK
[2025-12-23 08:00:46] Telechargement des donnees AFCON...
[2025-12-23 08:00:50] AFCON: OK
[2025-12-23 08:00:50] === MISE A JOUR TERMINEE AVEC SUCCES ===
```

---

## 🎯 Résultat

Chaque matin à 8h (ou l'heure que vous avez choisie), vos données seront automatiquement mises à jour.
Vous aurez toujours les derniers résultats sans rien faire !

---

## ⚠️ Note

Football-data.co.uk met à jour leurs fichiers **24-48h après les matchs**.
Donc un match du samedi soir sera dans vos données le lundi matin au plus tard.
