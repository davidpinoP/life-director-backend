const API_URL = 'http://127.0.0.1:8000';
let token = localStorage.getItem('token');
let currentUser = null;

// DOM Elements
const screens = {
    auth: document.getElementById('screen-auth'),
    onboarding: document.getElementById('screen-onboarding'),
    dashboard: document.getElementById('screen-dashboard')
};

// --- Navigation ---
function showScreen(screenName) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[screenName].classList.add('active');
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
        checkAuth();

    } catch (err) {
        errorMsg.textContent = err.message;
    }
});

document.getElementById('form-register').addEventListener('submit', async (e) => {
    e.preventDefault();
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
        document.getElementById('login-email').value = email;
        document.getElementById('login-password').value = password;
        document.getElementById('form-login').dispatchEvent(new Event('submit'));

    } catch (err) {
        errorMsg.textContent = err.message;
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

        // Now try to fetch the daily plan to see if we need onboarding
        loadDailyPlan();

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
checkAuth();
