// Football Club Platform - Frontend JavaScript

const API_BASE = '/api';
const API_KEY = 'dev-api-key-12345'; // In production, handle securely

let currentStep = 1;
let sessionData = {};
let players = [];
let performanceChart = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeTabs();
    loadPlayers();
});

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Load data if needed
    if (tabName === 'players') {
        loadPlayers();
    } else if (tabName === 'analytics') {
        loadAnalyticsPlayers();
    }
}

// API Helper
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }
        return await response.json();
    } catch (error) {
        console.error('API Call failed:', error);
        showAlert(error.message, 'error');
        throw error;
    }
}

// Alert System
function showAlert(message, type = 'success') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);

    setTimeout(() => alertDiv.remove(), 5000);
}

// Players Management
async function loadPlayers() {
    try {
        players = await apiCall('/players?limit=100');
        displayPlayers(players);
        updatePlayerSelects();
    } catch (error) {
        console.error('Failed to load players:', error);
    }
}

function displayPlayers(playersList) {
    const container = document.getElementById('players-list');
    container.innerHTML = '';

    if (playersList.length === 0) {
        container.innerHTML = '<p>Nessun giocatore trovato. Aggiungi il primo giocatore!</p>';
        return;
    }

    playersList.forEach(player => {
        const item = document.createElement('div');
        item.className = 'player-item';
        item.innerHTML = `
            <div class="player-info">
                <h4>${player.first_name} ${player.last_name}</h4>
                <p>Codice: ${player.code} | Ruolo: ${player.primary_role} | Categoria: ${player.category}</p>
            </div>
            <div class="player-actions">
                <button onclick="viewPlayerSessions('${player.id}')">Sessioni</button>
                <button class="secondary" onclick="editPlayer('${player.id}')">Modifica</button>
                <button class="danger" onclick="deletePlayer('${player.id}')">Elimina</button>
            </div>
        `;
        container.appendChild(item);
    });
}

function updatePlayerSelects() {
    const selects = [
        document.getElementById('session-player-code'),
        document.getElementById('analytics-player-select')
    ];

    selects.forEach(select => {
        if (!select) return;
        select.innerHTML = '<option value="">-- Seleziona giocatore --</option>';
        players.forEach(player => {
            const option = document.createElement('option');
            option.value = player.code;
            option.textContent = `${player.code} - ${player.first_name} ${player.last_name}`;
            select.appendChild(option);
        });
    });
}

// Wizard Form Management
function nextStep() {
    const currentContent = document.querySelector(`.wizard-content[data-step="${currentStep}"]`);
    const inputs = currentContent.querySelectorAll('input[required], select[required]');

    // Validate current step
    let isValid = true;
    inputs.forEach(input => {
        if (!input.value) {
            isValid = false;
            input.style.borderColor = 'red';
        } else {
            input.style.borderColor = '';
        }
    });

    if (!isValid) {
        showAlert('Compila tutti i campi obbligatori', 'error');
        return;
    }

    // Save current step data
    saveStepData(currentStep);

    // Move to next step
    if (currentStep < 7) {
        currentStep++;
        updateWizardUI();
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateWizardUI();
    }
}

function updateWizardUI() {
    // Hide all wizard contents
    document.querySelectorAll('.wizard-content').forEach(content => {
        content.style.display = 'none';
    });

    // Show current step
    document.querySelector(`.wizard-content[data-step="${currentStep}"]`).style.display = 'block';

    // Update progress
    document.querySelectorAll('.wizard-step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 < currentStep) {
            step.classList.add('completed');
        } else if (index + 1 === currentStep) {
            step.classList.add('active');
        }
    });

    // Update buttons
    document.getElementById('prev-btn').style.display = currentStep > 1 ? 'block' : 'none';
    document.getElementById('next-btn').style.display = currentStep < 7 ? 'block' : 'none';
    document.getElementById('submit-btn').style.display = currentStep === 7 ? 'block' : 'none';

    // If on summary step, show summary
    if (currentStep === 7) {
        showSummary();
    }
}

function saveStepData(step) {
    const content = document.querySelector(`.wizard-content[data-step="${step}"]`);
    const inputs = content.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
        if (input.name) {
            sessionData[input.name] = input.value || null;
        }
    });
}

function showSummary() {
    const summaryDiv = document.getElementById('summary-content');
    summaryDiv.innerHTML = `
        <div class="summary-section">
            <h4>Giocatore</h4>
            <p>Codice: ${document.getElementById('session-player-code').value}</p>
        </div>
        <div class="summary-section">
            <h4>Sessione</h4>
            <p>Data: ${sessionData.session_date}</p>
            <p>Tipo: ${sessionData.session_type}</p>
            <p>Minuti: ${sessionData.minutes_played}</p>
        </div>
        <div class="summary-section">
            <h4>Metriche Chiave</h4>
            <p>Distanza: ${sessionData.distance_km} km</p>
            <p>Sprint >25km/h: ${sessionData.sprints_over_25kmh}</p>
            <p>Passaggi: ${sessionData.passes_completed}/${sessionData.passes_attempted}</p>
            <p>RPE: ${sessionData.rpe}</p>
        </div>
    `;
}

// Submit Session
document.getElementById('session-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const payload = {
        player_code: document.getElementById('session-player-code').value,
        session: {
            session_date: sessionData.session_date,
            session_type: sessionData.session_type,
            minutes_played: parseInt(sessionData.minutes_played) || 0,
            coach_rating: parseFloat(sessionData.coach_rating) || null,
            notes: sessionData.notes || null,
            status: 'OK'
        },
        metrics_physical: {
            height_cm: parseFloat(sessionData.height_cm) || null,
            weight_kg: parseFloat(sessionData.weight_kg) || null,
            resting_hr_bpm: parseInt(sessionData.resting_hr_bpm) || 60,
            distance_km: parseFloat(sessionData.distance_km) || 0,
            sprints_over_25kmh: parseInt(sessionData.sprints_over_25kmh) || 0,
            yoyo_level: parseFloat(sessionData.yoyo_level) || null,
            rpe: parseFloat(sessionData.rpe) || 5,
            sleep_hours: parseFloat(sessionData.sleep_hours) || null
        },
        metrics_technical: {
            passes_attempted: parseInt(sessionData.passes_attempted) || 0,
            passes_completed: parseInt(sessionData.passes_completed) || 0,
            progressive_passes: parseInt(sessionData.progressive_passes) || 0,
            shots: parseInt(sessionData.shots) || 0,
            shots_on_target: parseInt(sessionData.shots_on_target) || 0,
            successful_dribbles: parseInt(sessionData.successful_dribbles) || 0,
            failed_dribbles: parseInt(sessionData.failed_dribbles) || 0,
            ball_losses: parseInt(sessionData.ball_losses) || 0,
            ball_recoveries: parseInt(sessionData.ball_recoveries) || 0
        },
        metrics_tactical: {
            xg: parseFloat(sessionData.xg) || null,
            xa: parseFloat(sessionData.xa) || null,
            pressures: parseInt(sessionData.pressures) || 0,
            interceptions: parseInt(sessionData.interceptions) || 0,
            involvement_pct: parseFloat(sessionData.involvement_pct) || null
        },
        metrics_psych: {
            attention_score: parseInt(sessionData.attention_score) || null,
            motivation: parseInt(sessionData.motivation) || null,
            stress_management: parseInt(sessionData.stress_management) || null,
            self_esteem: parseInt(sessionData.self_esteem) || null,
            team_leadership: parseInt(sessionData.team_leadership) || null,
            mood_pre: parseInt(sessionData.mood_pre) || null,
            mood_post: parseInt(sessionData.mood_post) || null
        }
    };

    try {
        const result = await apiCall('/sessions', 'POST', payload);
        showAlert('Sessione salvata con successo! Performance Index: ' + result.analytics_outputs.performance_index, 'success');

        // Reset form
        document.getElementById('session-form').reset();
        currentStep = 1;
        sessionData = {};
        updateWizardUI();

        // Switch to analytics tab
        setTimeout(() => switchTab('analytics'), 2000);
    } catch (error) {
        console.error('Failed to save session:', error);
    }
});

// Analytics
async function loadAnalyticsPlayers() {
    updatePlayerSelects();
}

async function loadPlayerAnalytics() {
    const playerId = document.getElementById('analytics-player-select').value;
    if (!playerId) {
        showAlert('Seleziona un giocatore', 'error');
        return;
    }

    // Find player object
    const player = players.find(p => p.code === playerId);
    if (!player) return;

    try {
        // Load trend data
        const trendData = await apiCall(`/analytics/player/${player.id}/trend?limit=10`);

        // Load summary data
        const summaryData = await apiCall(`/analytics/player/${player.id}/summary`);

        // Display chart
        displayPerformanceChart(trendData);

        // Display stats
        displayPlayerStats(summaryData);
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

function displayPerformanceChart(data) {
    const ctx = document.getElementById('performance-chart').getContext('2d');

    if (performanceChart) {
        performanceChart.destroy();
    }

    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => d.session_date),
            datasets: [
                {
                    label: 'Performance Index',
                    data: data.map(d => d.performance_index),
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.3
                },
                {
                    label: 'Rolling Average',
                    data: data.map(d => d.progress_index_rolling),
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.3,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Trend Performance Index'
                },
                legend: {
                    display: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function displayPlayerStats(summary) {
    const container = document.getElementById('player-stats');
    container.innerHTML = `
        <div class="stat-box">
            <h4>Media Performance</h4>
            <div class="value">${summary.avg_performance_index}</div>
        </div>
        <div class="stat-box">
            <h4>Max Performance</h4>
            <div class="value">${summary.max_performance_index}</div>
        </div>
        <div class="stat-box">
            <h4>Min Performance</h4>
            <div class="value">${summary.min_performance_index}</div>
        </div>
        <div class="stat-box">
            <h4>Sessioni Totali</h4>
            <div class="value">${summary.total_sessions}</div>
        </div>
        <div class="stat-box">
            <h4>Z-Score Attuale</h4>
            <div class="value">${summary.current_baseline_zscore ? summary.current_baseline_zscore.toFixed(2) : 'N/A'}</div>
        </div>
        <div class="stat-box">
            <h4>Allenamenti</h4>
            <div class="value">${summary.training_stats.count}</div>
            <p style="font-size: 14px;">Media: ${summary.training_stats.avg_performance}</p>
        </div>
        <div class="stat-box">
            <h4>Partite</h4>
            <div class="value">${summary.match_stats.count}</div>
            <p style="font-size: 14px;">Media: ${summary.match_stats.avg_performance}</p>
        </div>
    `;
}

// Export Player Data
async function exportPlayerData() {
    const playerCode = document.getElementById('analytics-player-select').value;
    if (!playerCode) {
        showAlert('Seleziona un giocatore', 'error');
        return;
    }

    const player = players.find(p => p.code === playerCode);
    if (!player) return;

    window.open(`${API_BASE}/export/sessions.csv?player_id=${player.id}`, '_blank');
}

// Duplicate Last Session
async function duplicateLastSession() {
    const playerCode = document.getElementById('session-player-code').value;
    if (!playerCode) {
        showAlert('Seleziona prima un giocatore', 'error');
        return;
    }

    const player = players.find(p => p.code === playerCode);
    if (!player) return;

    try {
        const sessions = await apiCall(`/sessions?player_id=${player.id}&limit=1`);
        if (sessions.length === 0) {
            showAlert('Nessuna sessione precedente trovata', 'error');
            return;
        }

        const lastSession = sessions[0];

        // Populate form with last session data
        if (lastSession.metrics_physical) {
            const phys = lastSession.metrics_physical;
            document.querySelector('[name="height_cm"]').value = phys.height_cm || '';
            document.querySelector('[name="weight_kg"]').value = phys.weight_kg || '';
            document.querySelector('[name="resting_hr_bpm"]').value = phys.resting_hr_bpm || 60;
            document.querySelector('[name="distance_km"]').value = phys.distance_km || 0;
        }

        showAlert('Dati ultima sessione caricati', 'success');
    } catch (error) {
        console.error('Failed to duplicate session:', error);
    }
}

// Player CRUD operations (stubs - implement as needed)
function viewPlayerSessions(playerId) {
    showAlert('Funzione in sviluppo', 'success');
}

function editPlayer(playerId) {
    showAlert('Funzione in sviluppo', 'success');
}

async function deletePlayer(playerId) {
    if (!confirm('Sei sicuro di voler eliminare questo giocatore?')) {
        return;
    }

    try {
        await apiCall(`/players/${playerId}`, 'DELETE');
        showAlert('Giocatore eliminato con successo', 'success');
        loadPlayers();
    } catch (error) {
        console.error('Failed to delete player:', error);
    }
}

function showNewPlayerForm() {
    showAlert('Funzione in sviluppo - usa le API direttamente per ora', 'success');
}
