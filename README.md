# ⚽ Football Predictor

**Système de prédiction de matchs de football utilisant des modèles statistiques avancés (Poisson + Elo)**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Fonctionnalités

### 🧠 Modèle de Prédiction Avancé
- **Système Elo dynamique** - Ratings mis à jour en temps réel
- **Analyse Head-to-Head** - Pondère les confrontations directes (30%)
- **Forme récente** - Les 5 derniers matchs comptent x2
- **Pondération temporelle** - Matchs récents = plus d'importance
- **Sélection intelligente** - Scores contextuels ET précis

### 🏆 7 Compétitions Supportées
- ⚽ **Premier League** (Angleterre)
- ⚽ **La Liga** (Espagne)
- ⚽ **Serie A** (Italie)
- ⚽ **Bundesliga** (Allemagne)
- ⚽ **Ligue 1** (France)
- ⚽ **Ligue 2** (France)
- 🏆 **CAN / AFCON** (avec avantage pays organisateur)

### 📊 Prédictions Fournies
- **Top 2 scores** les plus probables avec pourcentages
- **Expected Goals (xG)** pour chaque équipe
- **Probabilités** : Victoire Domicile / Nul / Victoire Extérieur
- **Conseils de paris** : Over/Under, Double Chance

---

## 🚀 Installation

### Prérequis
- Python 3.11+
- pip

### Setup
```bash
# Cloner le repository
git clone https://github.com/axel-batteux/Football_Predictor.git
cd Football_Predictor

# Installer les dépendances
pip install -r requirements.txt

# Télécharger les données (automatique au premier lancement)
python src/download_data.py
python src/download_afcon_data.py
```

---

## 💻 Utilisation

### Interface Web (Recommandé)
```bash
python app.py
```
Ouvrez votre navigateur sur : **http://localhost:5000**

### Ligne de commande
```bash
python main.py
```

### Exemple Python
```python
from src.model import Ligue1Predictor

# Charger le modèle
predictor = Ligue1Predictor(league_code='E0')  # Premier League

# Prédire un match
result = predictor.predict_match('Arsenal', 'Chelsea')

print(f"Score probable: {result['most_likely_score']}")
print(f"xG: {result['expected_goals_home']} - {result['expected_goals_away']}")
print(f"Victoire Arsenal: {result['win_prob']}%")
```

---

## 🔄 Mise à Jour Automatique des Données

### Setup (Windows)
Le système peut automatiquement télécharger les dernières données chaque jour :

**Option 1 : Au démarrage de Windows**
```bash
# Créer un raccourci de auto_update_silent.vbs dans:
shell:startup
```

**Option 2 : Planificateur de tâches**
Voir `AUTO_UPDATE_SETUP.md` pour les instructions détaillées.

---

## 📈 Performance

**Tests sur CAN 2025 :**
| Match | Prédiction | Résultat Réel | Status |
|-------|------------|---------------|--------|
| Maroc - Comores | 2-0 (19.8%) | 2-0 | ✅ EXACT |
| Sénégal - Botswana | 3-0 (16.5%) | 3-0 | ✅ EXACT |
| RD Congo - Bénin | 1-0 (15%) | 1-0 | ✅ EXACT |
| Nigeria - Tanzanie | 2-0 (20.5%) | 2-1 | ✅ Proche |

**4/4 vainqueurs prédits correctement** 🎯

---

## 🏗️ Architecture

```
Football_Predictor/
├── src/
│   ├── model.py              # Modèle principal (Poisson + Elo)
│   ├── elo.py                # Système de rating Elo
│   ├── download_data.py      # Téléchargement données ligues
│   ├── download_afcon_data.py # Téléchargement données AFCON
│   └── tournament_sim.py     # Simulation de tournois
├── static/
│   ├── style.css            # Design moderne dark mode
│   └── script.js            # Interface interactive
├── templates/
│   └── index.html           # Page web
├── data/                    # Données CSV historiques
├── app.py                   # Serveur Flask
├── main.py                  # Interface CLI
└── requirements.txt         # Dépendances Python
```

---

## 🧮 Détails Techniques

### Algorithme de Prédiction
1. **Distribution de Poisson** pour calculer les probabilités de score
2. **Système Elo** pour ajuster selon la force des équipes
   - K-factor dynamique basé sur l'importance du match
   - Multiplicateur selon la différence de buts
3. **Pondération temporelle** : 
   - 0-6 mois : x3
   - 6-18 mois : x2
   - Plus ancien : x1
4. **Boost forme récente** : Derniers 5 matchs x2

### Sources de Données
- **Ligues européennes** : [football-data.co.uk](https://www.football-data.co.uk/)
- **Données internationales** : [GitHub - martj42](https://github.com/martj42/international_results)

---

## 🛠️ Technologies

- **Backend** : Python 3.11, Flask
- **Calculs** : NumPy, Pandas, SciPy (Poisson)
- **Frontend** : HTML5, CSS3 (Dark Mode), Vanilla JavaScript
- **Data** : CSV, API REST

---

## 📝 TODO

- [ ] Intégration ML (XGBoost/Random Forest)
- [ ] API publique
- [ ] Données joueurs (blessures, valeur marchande)
- [ ] Graphiques historiques
- [ ] Support Champions League / Europa League
- [ ] Mode mobile natif

---

## 👤 Auteur

**Axel Batteux**
- GitHub: [@axel-batteux](https://github.com/axel-batteux)

---

## 📄 License

MIT License - Voir [LICENSE](LICENSE) pour plus de détails

---

## 🙏 Remerciements

- football-data.co.uk pour les données des ligues
- martj42 pour les résultats internationaux
- La communauté open source

---

**⭐ Si ce projet vous aide, n'hésitez pas à laisser une étoile !**
