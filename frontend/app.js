const API_URL = 'http://127.0.0.1:8000';
let token = localStorage.getItem('token');
let currentUser = null;

// DOM Elements
const screens = {
    auth: document.getElementById('screen-auth'),
    onboarding: document.getElementById('screen-onboarding'),
    dashboard: document.getElementById('screen-dashboard'),
    history: document.getElementById('screen-history'),
    menu: document.getElementById('screen-menu'),
    stats: document.getElementById('screen-stats'),
    achievements: document.getElementById('screen-achievements')
};

// --- Navigation ---
function showScreen(screenName) {
    Object.values(screens).forEach(s => s && s.classList.remove('active'));

    if (screens[screenName]) {
        screens[screenName].classList.add('active');
    } else {
        console.error(`Screen "${screenName}" not found in DOM.`);
    }
}

// --- Auth Logic ---
const authTabs = document.querySelectorAll('.tab');
const authForms = document.querySelectorAll('.form');
const errorMsg = document.getElementById('auth-error');

authTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        authTabs.forEach(t => t.classList.remove('active'));
        authForms.forEach(f => f.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`form-${tab.dataset.tab}`).classList.add('active');
        errorMsg.textContent = '';
    });
});

document.getElementById('form-login').addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log("Intentando login...");
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Error en login');

        token = data.access_token;
        localStorage.setItem('token', token);
        console.log("Login exitoso");
        checkAuth();

    } catch (err) {
        console.error("Login error:", err);
        errorMsg.textContent = err.message;
        alert(`Error: ${err.message}`); // Force visibility
    }
});

document.getElementById('form-register').addEventListener('submit', async (e) => {
    e.preventDefault();
    console.log("Intentando registro...");
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const res = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        if (!res.ok) {
            const data = await res.json();
            throw new Error(data.detail || 'Error en registro');
        }

        // Auto login after register
        console.log("Registro exitoso, autologin...");
        document.getElementById('login-email').value = email;
        document.getElementById('login-password').value = password;
        document.getElementById('form-login').dispatchEvent(new Event('submit'));

    } catch (err) {
        console.error("Register error:", err);
        errorMsg.textContent = err.message;
        alert(`Error Registro: ${err.message}`);
    }
});

document.getElementById('btn-logout').addEventListener('click', () => {
    localStorage.removeItem('token');
    token = null;
    showScreen('auth');
});

// --- Main App Logic ---
async function checkAuth() {
    if (!token) {
        showScreen('auth');
        return;
    }

    try {
        // Check health/status as simple token check proxy or just try getting plan
        // Ideally we would have a /me endpoint, but we can assume valid if we have token
        // and handle 401 later.

        // Let's try to get status to verify connection
        await fetch(`${API_URL}/status`);

        // Update: Now we go to Menu (Home) instead of loading plan immediately
        // Update: Now we go to Menu (Home) instead of loading plan immediately
        showScreen('menu');
        loadHomeSummaries(); // Refresh data for cards

        // We can optionally pre-fetch to update the badge or state but it's not strictly necessary for v1 home


    } catch (err) {
        console.error(err);
        showScreen('auth');
    }
}

// --- Onboarding ---
const activitiesList = [];
document.getElementById('add-activity').addEventListener('click', () => {
    const activity = prompt("Nombre de la actividad:");
    if (activity) {
        activitiesList.push({ name: activity, hours_per_week: 5, aligned_with_goal: true }); // Simplified
        renderActivities();
    }
});

function renderActivities() {
    const container = document.getElementById('activities-list');
    container.innerHTML = activitiesList.map(a => `<div class="activity-tag">${a.name}</div>`).join('');
}

document.getElementById('form-onboarding').addEventListener('submit', async (e) => {
    e.preventDefault();

    const data = {
        primary_goal: document.getElementById('primary-goal').value,
        goal_deadline: document.getElementById('goal-deadline').value,
        hours_work: parseFloat(document.getElementById('hours-work').value),
        hours_sleep: parseFloat(document.getElementById('hours-sleep').value),
        current_activities: activitiesList,
        main_obstacle: document.getElementById('main-obstacle').value,
        peak_energy_time: document.getElementById('peak-energy').value
    };

    // Validación: Mínimo 1 actividad requerida
    if (activitiesList.length === 0) {
        // Añadimos "Trabajo principal" por defecto si no ha puesto nada
        activitiesList.push({
            name: "Trabajo/Estudio principal",
            hours_per_week: data.hours_work * 5,
            priority: 10,
            aligned_with_goal: true
        });
    }

    // Actualizamos el objeto data con la lista (posiblemente modificada)
    data.current_activities = activitiesList;

    try {
        const res = await fetch(`${API_URL}/onboarding`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        if (!res.ok) throw new Error('Error en onboarding');

        loadDailyPlan();

    } catch (err) {
        alert(err.message);
    }
});

// --- Dashboard & Daily Plan ---
async function loadDailyPlan() {
    const loading = document.getElementById('loading-plan');
    const content = document.getElementById('plan-content');
    const noPlan = document.getElementById('no-plan');

    // Reset states
    loading.classList.remove('active');

    try {
        // Intentar obtener plan de hoy
        const res = await fetch(`${API_URL}/director/today`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const plan = await res.json();
            showScreen('dashboard');
            updateDate();
            renderPlan(plan);
            content.classList.remove('hidden');
            noPlan.classList.add('hidden');
            return;
        }

        // Si no hay plan (404), verificar si tiene onboarding hecho
        if (res.status === 404) {
            // Verificamos onboarding intentando obtener el diagnóstico
            const diagRes = await fetch(`${API_URL}/onboarding/diagnosis`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (diagRes.ok) {
                // Tiene onboarding, pero no plan -> Mostrar dashboard vacio
                showScreen('dashboard');
                updateDate();
                noPlan.classList.remove('hidden');
                content.classList.add('hidden');
            } else {
                // No tiene onboarding -> Redirigir a onboarding
                showScreen('onboarding');
            }
            return;
        }

        // Otros errores (401, etc)
        if (res.status === 401) {
            localStorage.removeItem('token');
            showScreen('auth');
        }

    } catch (err) {
        console.error(err);
        showScreen('auth');
    }
}

document.getElementById('btn-generate').addEventListener('click', async () => {
    const loading = document.getElementById('loading-plan');
    const noPlan = document.getElementById('no-plan');

    noPlan.classList.add('hidden');
    loading.classList.add('active');

    try {
        const res = await fetch(`${API_URL}/director/daily-plan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                available_hours: 12,
                energy_level: 8,
                existing_commitments: []
            })
        });

        if (!res.ok) throw new Error('Error generando plan');

        const plan = await res.json();
        renderPlan(plan);
        document.getElementById('plan-content').classList.remove('hidden');

    } catch (err) {
        alert(err.message);
        noPlan.classList.remove('hidden');
    } finally {
        loading.classList.remove('active');
    }
});

let currentPlanId = null;
let currentPlanItems = [];

function renderPlan(plan) {
    currentPlanId = plan.id;
    currentPlanItems = plan.si_hoy;

    document.getElementById('regla-clave').textContent = plan.regla_clave;

    document.getElementById('list-si-hoy').innerHTML = plan.si_hoy
        .map(item => `<li>${item}</li>`).join('');

    document.getElementById('list-no-hoy').innerHTML = plan.no_hoy
        .map(item => `<li>${item}</li>`).join('');

    // Sort schedule
    const sortedTimes = Object.keys(plan.horarios).sort();
    document.getElementById('schedule').innerHTML = sortedTimes
        .map(time => `
            <div class="schedule-item">
                <div class="time">${time}</div>
                <div class="activity">${plan.horarios[time]}</div>
            </div>
        `).join('');

    // Load active achievement for dashboard mini card
    loadActiveAchievementMini();
}

function updateDate() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('current-date').textContent = new Date().toLocaleDateString('es-ES', options);
}

// --- Feedback ---
const modal = document.getElementById('modal-feedback');
document.getElementById('btn-feedback').addEventListener('click', () => {
    modal.classList.add('active');

    // Populate tasks
    const container = document.getElementById('feedback-tasks');
    container.innerHTML = currentPlanItems.map((item, index) => `
        <label class="feedback-task">
            <input type="checkbox" value="${item}">
            <span>${item}</span>
        </label>
    `).join('');

    // Checkbox styling logic
    document.querySelectorAll('.feedback-task input').forEach(cb => {
        cb.addEventListener('change', (e) => {
            e.target.parentElement.classList.toggle('checked', e.target.checked);
        });
    });
});

document.getElementById('close-modal').addEventListener('click', () => {
    modal.classList.remove('active');
});

// Sliders and Toggles
['energy-start', 'energy-end'].forEach(id => {
    const slider = document.getElementById(id);
    const output = document.getElementById(`${id}-value`);
    slider.addEventListener('input', () => output.textContent = slider.value);
});

document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const parent = e.target.parentElement;
        parent.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('selected'));
        e.target.classList.add('selected');

        const val = e.target.dataset.value === 'true';
        document.getElementById('had-blockers').value = val;

        if (id = parent.nextElementSibling) {
            if (id.id === 'blocker-details') {
                id.classList.toggle('hidden', !val);
            }
        }

        const blockerDetails = document.getElementById('blocker-details');
        if (blockerDetails) blockerDetails.classList.toggle('hidden', !val);
    });
});

document.getElementById('form-feedback').addEventListener('submit', async (e) => {
    e.preventDefault();

    const completed = Array.from(document.querySelectorAll('#feedback-tasks input:checked')).map(cb => cb.value);
    const skipped = currentPlanItems.filter(item => !completed.includes(item));

    const payload = {
        plan_id: currentPlanId,
        completed_items: completed,
        skipped_items: skipped,
        had_blockers: document.getElementById('had-blockers').value === 'true',
        blocker_type: document.getElementById('blocker-type').value,
        blocker_details: "",
        energy_at_start: parseInt(document.getElementById('energy-start').value),
        energy_at_end: parseInt(document.getElementById('energy-end').value),
        sleep_hours: parseFloat(document.getElementById('feedback-sleep').value),
        sleep_quality: 5
    };

    try {
        const res = await fetch(`${API_URL}/director/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Error al guardar feedback');

        alert('Día registrado');
        modal.classList.remove('active');

    } catch (err) {
        alert(err.message);
    }
});

// Setup
// --- History Logic ---
const historyScreen = document.getElementById('screen-history');
const historyList = document.getElementById('history-list');



document.querySelectorAll('.nav-back').forEach(btn => {
    btn.addEventListener('click', () => {
        showScreen(btn.dataset.target);
    });
});

async function loadHistory() {
    historyList.innerHTML = '<div class="loading-history" style="color: white; padding: 20px; text-align: center;">Cargando historial...</div>';

    try {
        console.log("Fetching history...");
        const res = await fetch(`${API_URL}/director/history?limit=30`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`Error backend (${res.status}): ${errText}`);
        }

        const history = await res.json();
        console.log("History received:", history);
        renderHistory(history);

    } catch (err) {
        console.error("History error:", err);
        historyList.innerHTML = `<div class="error-message" style="color: red; padding: 20px;">Error: ${err.message}</div>`;
    }
}

function renderHistory(items) {
    if (items.length === 0) {
        historyList.innerHTML = '<p style="text-align:center; padding:20px; color:var(--text-secondary)">Aún no tienes historial.</p>';
        return;
    }

    historyList.innerHTML = items.map(item => {
        const date = new Date(item.date).toLocaleDateString();
        const rule = item.regla_clave;

        let badgeHtml = '';
        let badgeColor = 'var(--secondary-color)';

        if (item.completion_rate !== null) {
            const pct = Math.round(item.completion_rate * 100);
            badgeHtml = `${pct}%`;

            if (pct >= 80) badgeColor = 'var(--success-color)';
            else if (pct >= 50) badgeColor = '#f57c00'; // Orange
            else badgeColor = 'var(--error-color)';
        } else {
            badgeHtml = '-';
        }

        // Data attribute stores the full item for click handler
        // Using replace to escape potential quotes in json stringify
        const jsonItem = JSON.stringify(item).replace(/"/g, '&quot;');

        return `
            <div class="history-card" onclick="openHistoryDetail('${item.id}')">
                <div>
                    <div class="card-date">${date}</div>
                    <div class="card-rule">${rule}</div>
                </div>
                <div class="completion-badge" style="background-color: ${badgeColor}">
                    ${badgeHtml}
                </div>
            </div>
        `;
    }).join('');

    // Store items in memory for detail view
    window.historyItems = items;
}

// Global function for onclick
window.openHistoryDetail = (id) => {
    const item = window.historyItems.find(i => i.id === id);
    if (!item) return;

    const modal = document.getElementById('modal-day-detail');

    // Populate modal
    document.getElementById('detail-date').textContent = new Date(item.date).toLocaleDateString(undefined, {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
    });

    document.getElementById('detail-rule').textContent = item.regla_clave;

    // Score Badge
    const scoreBadge = document.getElementById('detail-score');
    if (item.completion_rate !== null) {
        const pct = Math.round(item.completion_rate * 100);
        scoreBadge.textContent = `${pct}% CUMPLIDO`;
        scoreBadge.style.backgroundColor = pct >= 80 ? 'var(--success-color)' : (pct >= 50 ? '#f57c00' : 'var(--error-color)');
    } else {
        scoreBadge.textContent = 'SIN REGISTRAR';
        scoreBadge.style.backgroundColor = 'var(--secondary-color)';
    }

    // Tasks List
    const taskContainer = document.getElementById('detail-tasks');
    // We assume backend returns completion status inside the history object if we expand it later.
    // BUT right now PlanHistoryItem only has optional completion_rate/had_blockers.
    // It doesn't have the list of WHICH items were completed (that's in Feedback body, but our history endpoint returns PlanHistoryItem).
    // The current endpoint returns Plan (with si_hoy) + Feedback Summary.
    // To show which ones were done, we need to either:
    // A) Update backend to return full feedback details
    // B) Fetch feedback details on click.
    // Given the request, we should probably just show the plan's tasks and assume they were done *IF* feedback logic matches, but we don't know existing specific completions.

    // Simplification for V1: Show original tasks list.
    // If we want to show strikethrough for completed, we need completed_items from feedback.

    // Let's implement fetch detail if needed, or just list them.
    // The user said "see all tasks".

    taskContainer.innerHTML = item.si_hoy.map(task => `<li>${task}</li>`).join('');
    document.getElementById('detail-forbidden').innerHTML = item.no_hoy.map(task => `<li>${task}</li>`).join('');

    // Blocker
    const blockerSection = document.getElementById('detail-blocker-section');
    if (item.had_blockers) {
        blockerSection.classList.remove('hidden');
        document.getElementById('detail-blocker').textContent = "Se reportó un bloqueo ese día.";
    } else {
        blockerSection.classList.add('hidden');
    }

    modal.classList.add('active');
};

document.getElementById('close-detail-modal').addEventListener('click', () => {
    document.getElementById('modal-day-detail').classList.remove('active');
});

// Setup

// --- Menu & Stats Logic ---

// Global navigation for HTML onclicks
window.goToScreen = (screenName) => {
    if (screenName === 'dashboard') {
        loadDailyPlan();
    } else if (screenName === 'history') {
        loadHistory();
        showScreen('history');
    } else if (screenName === 'stats') {
        loadStats();
        showScreen('stats');
    } else if (screenName === 'achievements') {
        loadAchievements();
        showScreen('achievements');
    } else {
        showScreen(screenName);
    }
};

document.getElementById('btn-logout-menu').addEventListener('click', () => {
    localStorage.removeItem('token');
    token = null;
    showScreen('auth');
});


async function loadStats() {
    const loading = document.getElementById('loading-stats');
    const content = document.getElementById('stats-content');

    loading.classList.remove('hidden'); // Ensure loading is visible
    content.classList.add('hidden');

    try {
        const res = await fetch(`${API_URL}/feedback/analysis`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) throw new Error('No hay suficientes datos aún.');

        const data = await res.json();

        // Render Stats
        document.getElementById('stat-sleep').textContent =
            data.average_sleep ? `${data.average_sleep.toFixed(1)} h` : '--';

        document.getElementById('stat-completion').textContent =
            `${Math.round(data.average_completion * 100)}%`;

        document.getElementById('stat-recommendation').textContent =
            data.recommendation || "Sigue registrando días para obtener análisis.";

        // Energy/Sleep Message
        const sleepMsg = document.getElementById('stat-sleep-msg');
        if (data.sleep_trend === 'declining') {
            sleepMsg.textContent = "Tendencia a la baja. Cuidado.";
            sleepMsg.style.color = 'var(--error-color)';
        } else {
            sleepMsg.textContent = "Estable.";
            sleepMsg.style.color = 'var(--success-color)';
        }

        loading.classList.add('hidden'); // Custom CSS might need fix if 'active' class used commonly
        // My CSS for .loading uses .active to show. 
        // Logic: .loading (display:none), .loading.active (display:block)
        // So I should use .active

        loading.style.display = 'none'; // Force hide for safety or use class logic
        content.classList.remove('hidden');

    } catch (err) {
        console.error(err);
        loading.innerHTML = `<p style="color:red">${err.message}</p>`;
    }
}

// Fix: Ensure loading class logic is consistent
// In accessible CSS: .loading { display: none } .loading.active { display: block }
// So to show: add active. To hide: remove active.

// Setup
checkAuth();

async function loadHomeSummaries() {
    // 1. Plan Summary
    const planEl = document.getElementById('summary-plan');
    if (!planEl) return;
    try {
        const res = await fetch(`${API_URL}/director/today`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (res.ok) {
            const plan = await res.json();
            const doneCount = plan.si_hoy.length;
            planEl.innerText = `${doneCount} Órdenes Activas.`;
            planEl.style.color = 'var(--primary-color)';
        } else if (res.status === 404) {
            planEl.innerText = "Sin plan (Generar)";
            planEl.style.color = 'var(--text-secondary)';
        } else {
            planEl.innerText = "Estado desconocido";
        }
    } catch { planEl.innerText = "--"; }

    // 2. Stats Summary
    const statsEl = document.getElementById('summary-stats');
    if (statsEl) {
        try {
            const res = await fetch(`${API_URL}/feedback/analysis`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (res.ok) {
                const data = await res.json();
                const sleep = data.average_sleep ? `${data.average_sleep.toFixed(1)}h` : '--';
                const comp = Math.round(data.average_completion * 100);
                statsEl.innerText = `Sueño: ${sleep} | ${comp}% Cumplido`;
            } else {
                statsEl.innerText = "Sin datos suficientes";
            }
        } catch { statsEl.innerText = "--"; }
    }

    // 3. History Summary
    const histEl = document.getElementById('summary-history');
    if (histEl) {
        try {
            const res = await fetch(`${API_URL}/director/history?limit=1`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (res.ok) {
                const list = await res.json();
                if (list.length > 0) {
                    const date = new Date(list[0].date).toLocaleDateString();
                    histEl.innerText = `Último registro: ${date}`;
                } else {
                    histEl.innerText = "Sin historial";
                }
            }
        } catch { histEl.innerText = "--"; }
    }

    // 4. Achievement Summary
    const achEl = document.getElementById('summary-achievements');
    if (achEl) {
        try {
            const res = await fetch(`${API_URL}/achievements/active`, { headers: { 'Authorization': `Bearer ${token}` } });
            if (res.ok) {
                const ach = await res.json();
                achEl.innerText = `${ach.title} (${Math.round(ach.progress)}%)`;
            } else {
                achEl.innerText = "Empieza hoy";
            }
        } catch { achEl.innerText = "--"; }
    }
}

// --- Achievements Logic ---
async function loadAchievements() {
    const listEl = document.getElementById('achievements-list');
    listEl.innerHTML = '<div class="loading active"><div class="spinner"></div><p>Cargando tus metas...</p></div>';

    try {
        const res = await fetch(`${API_URL}/achievements/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) throw new Error('No se pudieron cargar los logros');

        const achievements = await res.json();
        renderAchievementsList(achievements);

    } catch (err) {
        listEl.innerHTML = `<p class="error-message">${err.message}</p>`;
    }
}

function renderAchievementsList(items) {
    const listEl = document.getElementById('achievements-list');

    if (items.length === 0) {
        listEl.innerHTML = '<p style="text-align:center; padding:20px; color:var(--text-secondary)">Completa el onboarding para ver tu roadmap.</p>';
        return;
    }

    listEl.innerHTML = items.map(item => {
        const statusClass = item.is_active ? 'active' : (item.is_unlocked ? 'unlocked' : 'locked');
        const progress = Math.round(item.progress);

        return `
            <div class="achievement-card ${statusClass}">
                <div class="achievement-month-tag">Mes ${item.month_number}</div>
                <div class="achievement-title">${item.title}</div>
                <div class="achievement-desc">${item.description}</div>
                <div class="achievement-progress-container">
                    <div class="progress-bar-label">
                        <span>Progreso</span>
                        <span>${progress}%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: ${progress}%"></div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadActiveAchievementMini() {
    const card = document.getElementById('active-achievement-card');
    const titleEl = document.getElementById('active-achievement-title');
    const pctEl = document.getElementById('active-achievement-pct');
    const barEl = document.getElementById('active-achievement-progress');

    try {
        const res = await fetch(`${API_URL}/achievements/active`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (res.ok) {
            const ach = await res.json();
            titleEl.textContent = ach.title;
            pctEl.textContent = `${Math.round(ach.progress)}%`;
            barEl.style.width = `${ach.progress}%`;
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    } catch {
        card.classList.add('hidden');
    }
}
