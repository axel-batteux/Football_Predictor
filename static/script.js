let selectedCompetition = null;

function selectCompetition(key) {
    selectedCompetition = key;

    // Update UI
    document.querySelectorAll('.comp-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.classList.add('selected');

    // Show form
    document.getElementById('match-form').style.display = 'block';
    document.getElementById('result').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    // Load teams for autocomplete
    fetch(`/teams/${key}`)
        .then(r => r.json())
        .then(data => {
            const datalist = document.getElementById('teams-list');
            datalist.innerHTML = '';
            data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team;
                datalist.appendChild(option);
            });
        });
}

async function predict() {
    const homeTeam = document.getElementById('home-team').value.trim();
    const awayTeam = document.getElementById('away-team').value.trim();

    if (!selectedCompetition) {
        showError('Sélectionnez une compétition d\'abord');
        return;
    }

    if (!homeTeam || !awayTeam) {
        showError('Entrez les deux équipes');
        return;
    }

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                competition: selectedCompetition,
                home_team: homeTeam,
                away_team: awayTeam
            })
        });

        const data = await response.json();

        if (response.ok) {
            displayResult(data);
        } else {
            showError(data.error);
        }
    } catch (error) {
        showError('Erreur de connexion au serveur');
    }
}

function displayResult(data) {
    document.getElementById('error').style.display = 'none';
    document.getElementById('result').style.display = 'block';

    // Match title
    document.getElementById('match-title').textContent =
        `${data.home_team} vs ${data.away_team}`;

    // Probabilities
    document.getElementById('prob-home').style.width = data.win_prob + '%';
    document.getElementById('prob-home-val').textContent = data.win_prob + '%';

    document.getElementById('prob-draw').style.width = data.draw_prob + '%';
    document.getElementById('prob-draw-val').textContent = data.draw_prob + '%';

    document.getElementById('prob-away').style.width = data.loss_prob + '%';
    document.getElementById('prob-away-val').textContent = data.loss_prob + '%';

    // Stats - Show top 2 scores
    document.getElementById('score').innerHTML =
        `<strong>${data.most_likely_score}</strong> (${data.score_prob}%)<br>` +
        `<span style="font-size: 0.9em; opacity: 0.8;">${data.second_likely_score} (${data.second_score_prob}%)</span>`;
    document.getElementById('xg').textContent =
        `${data.expected_goals_home} - ${data.expected_goals_away}`;

    // Tip
    let tip = '';
    const totalXg = data.expected_goals_home + data.expected_goals_away;

    if (data.win_prob > 60) {
        tip = `💡 Victoire ${data.home_team} (forte probabilité)`;
    } else if (data.loss_prob > 60) {
        tip = `💡 Victoire ${data.away_team} (forte probabilité)`;
    } else {
        tip = '⚠️ Match serré, privilégier le Nul ou Double Chance';
    }

    if (totalXg < 2.0) {
        tip += '<br>📉 Under 2.5 Buts recommandé';
    } else if (totalXg > 2.8) {
        tip += '<br>📈 Over 2.5 Buts recommandé';
    }

    document.getElementById('tip').innerHTML = tip;

    // Scroll to result
    document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = '❌ ' + message;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

// --- TENNIS LOGIC ---

let currentSurface = 'Hard';

function switchMode(mode) {
    // Buttons
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    if (mode === 'football') {
        document.querySelectorAll('.mode-btn')[0].classList.add('active');
        document.getElementById('football-container').style.display = 'block';
        document.getElementById('tennis-container').style.display = 'none';
        document.getElementById('tennis-result').style.display = 'none';
        document.getElementById('result').style.display = 'none';
    } else {
        document.querySelectorAll('.mode-btn')[1].classList.add('active');
        document.getElementById('football-container').style.display = 'none';
        document.getElementById('tennis-container').style.display = 'block';
        document.getElementById('result').style.display = 'none';
        // Hide previous tennis result if any
        document.getElementById('tennis-result').style.display = 'none';
    }
}

function selectSurface(surface) {
    currentSurface = surface;
    document.querySelectorAll('.surface-btn').forEach(btn => {
        btn.classList.remove('selected');
        if (btn.textContent === surface) btn.classList.add('selected');
    });
}

async function predictTennis() {
    const p1 = document.getElementById('p1-input').value.trim();
    const p2 = document.getElementById('p2-input').value.trim();

    if (!p1 || !p2) {
        showError('Entrez le nom des deux joueurs');
        return;
    }

    try {
        const response = await fetch('/predict_tennis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player1: p1,
                player2: p2,
                surface: currentSurface
            })
        });

        const data = await response.json();

        if (response.ok) {
            displayResultTennis(data);
        } else {
            showError(data.error);
        }
    } catch (error) {
        showError('Erreur serveur tennis');
    }
}

function displayResultTennis(data) {
    document.getElementById('error').style.display = 'none';
    document.getElementById('tennis-result').style.display = 'block';

    // Title
    document.getElementById('tennis-match-title').textContent = `${data.player1} vs ${data.player2}`;
    document.getElementById('res-surface').textContent = `Surface: ${data.surface}`;

    // Players Names
    document.getElementById('p1-name-display').textContent = data.player1;
    document.getElementById('p2-name-display').textContent = data.player2;

    // Elo
    document.getElementById('elo-p1').textContent = `Elo: ${data.elo1}`;
    document.getElementById('elo-p2').textContent = `Elo: ${data.elo2}`;

    // Bars
    document.getElementById('prob-p1').style.width = data.win_prob1 + '%';
    document.getElementById('prob-p1-val').textContent = data.win_prob1 + '%';

    document.getElementById('prob-p2').style.width = data.win_prob2 + '%';
    document.getElementById('prob-p2-val').textContent = data.win_prob2 + '%';

    document.getElementById('tennis-result').scrollIntoView({ behavior: 'smooth' });
}
