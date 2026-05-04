// Global state
let stats = {
    correct: 0,
    total: 0
};

let evalMode = false;

let currentConfig = {
    position: null,
    action: null,
    stackDepth: null,
    availableActions: []
};

// Eval multi-select state
let evalSelectedPositions = new Set();
let evalSelectedDepths = new Set();
let evalAllDepths = [];  // union of depths for selected positions

let currentHand = null;
let currentScenario = { action: null, label: null, position: null, stackDepth: null };

// DOM elements
const configScreen        = document.getElementById('config-screen');
const practiceScreen      = document.getElementById('practice-screen');
const positionSelect      = document.getElementById('position');
const actionSelect        = document.getElementById('action');
const stackDepthSelect    = document.getElementById('stack-depth');
const actionFormGroup     = document.getElementById('action-form-group');
const startBtn            = document.getElementById('start-btn');
const currentHandDisplay  = document.getElementById('current-hand');
const configDisplay       = document.getElementById('config-display');
const scenarioLabel       = document.getElementById('scenario-label');
const preflopQuestion     = document.getElementById('preflop-question');
const buttonGroup         = document.querySelector('.button-group');
const backBtn             = document.getElementById('back-btn');
const nextBtn             = document.getElementById('next-btn');
const feedbackDiv         = document.getElementById('feedback');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPositions();
    setupEventListeners();
});

function setupEventListeners() {
    document.getElementById('mode-classic').addEventListener('click', () => setMode('classic'));
    document.getElementById('mode-eval').addEventListener('click',   () => setMode('eval'));
    positionSelect.addEventListener('change', onPositionChange);
    actionSelect.addEventListener('change', onActionChange);
    stackDepthSelect.addEventListener('change', onStackDepthChange);
    startBtn.addEventListener('click', startPractice);
    nextBtn.addEventListener('click', loadNextHand);
    backBtn.addEventListener('click', backToMenu);
}

function setMode(mode) {
    evalMode = mode === 'eval';
    document.getElementById('mode-classic').classList.toggle('active', !evalMode);
    document.getElementById('mode-eval').classList.toggle('active', evalMode);

    // Classic-only controls
    document.getElementById('classic-position-group').style.display = evalMode ? 'none' : '';
    document.getElementById('classic-depth-group').style.display    = evalMode ? 'none' : '';
    actionFormGroup.style.display = evalMode ? 'none' : '';

    // Eval-only controls
    document.getElementById('eval-position-group').style.display = evalMode ? '' : 'none';
    document.getElementById('eval-depth-group').style.display    = evalMode ? '' : 'none';

    // Reset classic selects
    positionSelect.value = '';
    actionSelect.innerHTML = '<option value="">Choose action...</option>';
    actionSelect.disabled = true;
    stackDepthSelect.innerHTML = '<option value="">Choose stack depth...</option>';
    stackDepthSelect.disabled = true;
    startBtn.disabled = true;

    // Reset eval multi-select
    evalSelectedPositions.clear();
    evalSelectedDepths.clear();
    evalAllDepths = [];
    document.getElementById('eval-depths-buttons').innerHTML = '';

    if (evalMode) loadEvalPositions();
}

async function loadPositions() {
    try {
        const positions = await fetch('/api/positions').then(r => r.json());
        positions.forEach(pos => {
            const opt = document.createElement('option');
            opt.value = pos;
            opt.textContent = pos;
            positionSelect.appendChild(opt);
        });
    } catch (e) {
        console.error('Error loading positions:', e);
    }
}

async function loadEvalPositions() {
    try {
        const positions = await fetch('/api/positions').then(r => r.json());
        const container = document.getElementById('eval-positions-buttons');
        container.innerHTML = '';
        positions.forEach(pos => {
            const btn = document.createElement('button');
            btn.className = 'eval-toggle-btn';
            btn.textContent = pos;
            btn.dataset.value = pos;
            btn.addEventListener('click', () => toggleEvalPosition(pos, btn));
            container.appendChild(btn);
        });
    } catch (e) {
        console.error('Error loading eval positions:', e);
    }
}

async function toggleEvalPosition(pos, btn) {
    if (evalSelectedPositions.has(pos)) {
        evalSelectedPositions.delete(pos);
        btn.classList.remove('selected');
    } else {
        evalSelectedPositions.add(pos);
        btn.classList.add('selected');
    }
    await refreshEvalDepths();
    updateEvalStartBtn();
}

async function refreshEvalDepths() {
    // Collect union of stack depths for all selected positions
    const depthSet = new Set();
    for (const pos of evalSelectedPositions) {
        try {
            const depths = await fetch(`/api/eval/stack-depths/${pos}`).then(r => r.json());
            depths.forEach(d => depthSet.add(d));
        } catch (e) {
            console.error('Error loading eval stack depths:', e);
        }
    }
    evalAllDepths = [...depthSet].sort();

    // Remove depths no longer available
    for (const d of evalSelectedDepths) {
        if (!depthSet.has(d)) evalSelectedDepths.delete(d);
    }

    const container = document.getElementById('eval-depths-buttons');
    container.innerHTML = '';
    evalAllDepths.forEach(depth => {
        const btn = document.createElement('button');
        btn.className = 'eval-toggle-btn';
        btn.textContent = depth;
        btn.dataset.value = depth;
        if (evalSelectedDepths.has(depth)) btn.classList.add('selected');
        btn.addEventListener('click', () => toggleEvalDepth(depth, btn));
        container.appendChild(btn);
    });

    document.getElementById('eval-depth-group').style.display =
        evalSelectedPositions.size > 0 ? '' : 'none';
}

function toggleEvalDepth(depth, btn) {
    if (evalSelectedDepths.has(depth)) {
        evalSelectedDepths.delete(depth);
        btn.classList.remove('selected');
    } else {
        evalSelectedDepths.add(depth);
        btn.classList.add('selected');
    }
    updateEvalStartBtn();
}

function updateEvalStartBtn() {
    startBtn.disabled = evalSelectedPositions.size === 0 || evalSelectedDepths.size === 0;
}

async function onPositionChange() {
    const position = positionSelect.value;
    actionSelect.innerHTML = '<option value="">Choose action...</option>';
    stackDepthSelect.innerHTML = '<option value="">Choose stack depth...</option>';
    actionSelect.disabled = true;
    stackDepthSelect.disabled = true;
    startBtn.disabled = true;

    if (!position) return;

    try {
        const actions = await fetch(`/api/actions/${position}`).then(r => r.json());
        actions.forEach(action => {
            const opt = document.createElement('option');
            opt.value = action;
            opt.textContent = action;
            actionSelect.appendChild(opt);
        });
        actionSelect.disabled = false;
    } catch (e) {
        console.error('Error loading actions:', e);
    }
}

async function onActionChange() {
    const position = positionSelect.value;
    const action   = actionSelect.value;
    stackDepthSelect.innerHTML = '<option value="">Choose stack depth...</option>';
    stackDepthSelect.disabled = !action;
    startBtn.disabled = true;
    if (!action) return;
    try {
        const depths = await fetch(`/api/stack-depths/${position}/${action}`).then(r => r.json());
        depths.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d;
            opt.textContent = d;
            stackDepthSelect.appendChild(opt);
        });
    } catch (e) {
        console.error('Error loading stack depths:', e);
    }
}

function onStackDepthChange() {
    startBtn.disabled = !stackDepthSelect.value;
}

async function startPractice() {
    currentConfig.position   = evalMode ? null : positionSelect.value;
    currentConfig.action     = evalMode ? null : actionSelect.value;
    currentConfig.stackDepth = evalMode ? null : stackDepthSelect.value;

    try {
        let data;
        if (evalMode) {
            const positions   = [...evalSelectedPositions];
            const stack_depths = [...evalSelectedDepths];
            const res = await fetch('/api/eval/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ positions, stack_depths }),
            });
            data = await res.json();
            const posLabel   = positions.join(', ');
            const depthLabel = stack_depths.join(', ');
            configDisplay.textContent =
                `${posLabel} — Évaluation — ${depthLabel} (${data.scenario_count} scénarios)`;
        } else {
            const res = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    position:    currentConfig.position,
                    action:      currentConfig.action,
                    stack_depth: currentConfig.stackDepth,
                }),
            });
            data = await res.json();
            configDisplay.textContent =
                `${currentConfig.position} - ${currentConfig.action} - ${currentConfig.stackDepth} (${data.range_size} hands)`;
            currentConfig.availableActions = data.available_actions || ['in_range'];
            setupActionButtons();
        }

        if (data.success) {
            configScreen.classList.remove('active');
            practiceScreen.classList.add('active');
            loadNextHand();
        }
    } catch (e) {
        console.error('Error starting practice:', e);
    }
}

const ACTION_COLORS = {
    'in_range': '#28a745',
    'open':     '#28a745',
    '3bet':     '#d9534f',
    '4bet':     '#d9534f',
    'call':     '#5bc0de',
    'limp':     '#f0ad4e',
    'check':    '#f0ad4e',
    'raise':    '#d9534f',
    'fold':     '#dc3545',
    'default':  '#6c757d',
};

function getActionColor(action) {
    const base = action.split('_')[0];
    return ACTION_COLORS[base] || ACTION_COLORS[action] || ACTION_COLORS['default'];
}

function getActionLabel(action) {
    if (action === 'in_range') return '✓ In Range';
    if (action === 'fold')     return '✗ Fold';
    return action.charAt(0).toUpperCase() + action.slice(1).replace('_', ' ');
}

function setupActionButtons() {
    buttonGroup.innerHTML = '';
    const actions = [...currentConfig.availableActions];
    actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-large action-btn';
        btn.textContent = getActionLabel(action);
        btn.style.backgroundColor = getActionColor(action);
        btn.style.color = 'white';
        btn.dataset.action = action;
        btn.addEventListener('click', () => submitAnswer(action));
        buttonGroup.appendChild(btn);
    });

    // Always add Fold last
    const foldBtn = document.createElement('button');
    foldBtn.className = 'btn btn-large action-btn';
    foldBtn.textContent = '✗ Fold';
    foldBtn.style.backgroundColor = ACTION_COLORS['fold'];
    foldBtn.style.color = 'white';
    foldBtn.dataset.action = 'fold';
    foldBtn.addEventListener('click', () => submitAnswer('fold'));
    buttonGroup.appendChild(foldBtn);
}

async function loadNextHand() {
    feedbackDiv.classList.add('hidden');
    nextBtn.style.display = 'none';

    const btns = document.querySelectorAll('.action-btn');
    btns.forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.transform = 'none';
        btn.style.boxShadow = 'none';
        btn.style.border = 'none';
        btn.textContent = getActionLabel(btn.dataset.action);
        if (btn.dataset.action === 'fold') btn.textContent = '✗ Fold';
    });

    try {
        if (evalMode) {
            const data = await fetch('/api/eval/next-hand').then(r => r.json());
            currentHand     = data.hand;
            currentScenario = {
                action:     data.scenario_action,
                label:      data.scenario_label,
                position:   data.position,
                stackDepth: data.stack_depth,
            };
            currentConfig.availableActions = data.available_actions;

            scenarioLabel.textContent = `[${data.position} — ${data.stack_depth}] ${data.scenario_label}`;
            scenarioLabel.classList.remove('hidden');
            preflopQuestion.style.display = 'none';
            setupActionButtons();
        } else {
            const data = await fetch('/api/next-hand').then(r => r.json());
            currentHand = data.hand;
            scenarioLabel.classList.add('hidden');
            preflopQuestion.style.display = '';
        }
        currentHandDisplay.textContent = currentHand;
    } catch (e) {
        console.error('Error loading next hand:', e);
    }
}

async function submitAnswer(action) {
    document.querySelectorAll('.action-btn').forEach(btn => btn.disabled = true);

    try {
        let data;
        if (evalMode) {
            const res = await fetch('/api/eval/check-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    hand:            currentHand,
                    scenario_action: currentScenario.action,
                    user_action:     action,
                    position:        currentScenario.position,
                    stack_depth:     currentScenario.stackDepth,
                }),
            });
            data = await res.json();
        } else {
            const res = await fetch('/api/check-answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hand: currentHand, action }),
            });
            data = await res.json();
        }

        stats.total++;
        if (data.correct) stats.correct++;
        updateStats();
        showFeedback(data);
        nextBtn.style.display = 'block';
    } catch (e) {
        console.error('Error checking answer:', e);
    }
}

function showFeedback(data) {
    feedbackDiv.classList.remove('hidden', 'correct', 'incorrect');

    const actualAction = data.actual_action;
    const correctBtn = document.querySelector(`.action-btn[data-action="${actualAction}"]`);
    if (correctBtn) {
        correctBtn.style.opacity = '1';
        correctBtn.style.transform = 'scale(1.05)';
        correctBtn.style.boxShadow = '0 0 15px rgba(255, 215, 0, 0.7)';
        correctBtn.style.border = '3px solid white';
        if (!correctBtn.textContent.includes('✓') && !correctBtn.textContent.includes('✗')) {
            correctBtn.textContent = '✓ ' + correctBtn.textContent;
        }
    }

    document.querySelectorAll('.action-btn').forEach(btn => {
        if (btn !== correctBtn) btn.style.opacity = '0.5';
    });

    if (data.correct) {
        feedbackDiv.classList.add('correct');
        let html = '<div class="feedback-title">✓ CORRECT!</div>';
        if (data.user_action === 'fold') {
            html += `<div class="feedback-detail">Correct fold.</div>`;
        } else {
            html += `<div class="feedback-detail">Yes, it is ${data.user_action}.</div>`;
        }
        if (data.bottom_of_range) {
            html += `<div class="feedback-detail">Bottom of ${data.actual_action} range: <strong>${data.bottom_of_range}</strong></div>`;
        }
        feedbackDiv.innerHTML = html;
    } else {
        feedbackDiv.classList.add('incorrect');
        let html = '<div class="feedback-title">✗ INCORRECT</div>';
        html += `<div class="feedback-detail">You picked: <strong>${data.user_action}</strong></div>`;
        html += `<div class="feedback-detail">Actual: <strong>${data.actual_action}</strong></div>`;
        if (data.closest_hand) {
            html += `<div class="feedback-detail">Closest hand in range: <strong>${data.closest_hand}</strong></div>`;
        }
        feedbackDiv.innerHTML = html;
    }
}

function updateStats() {
    document.getElementById('correct').textContent  = stats.correct;
    document.getElementById('total').textContent    = stats.total;
    const accuracy = stats.total > 0 ? ((stats.correct / stats.total) * 100).toFixed(1) : 0;
    document.getElementById('accuracy').textContent = accuracy + '%';
}

function backToMenu() {
    practiceScreen.classList.remove('active');
    configScreen.classList.add('active');
    feedbackDiv.classList.add('hidden');
    nextBtn.style.display = 'none';
}
