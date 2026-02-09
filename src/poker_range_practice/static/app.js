// Global state
let stats = {
    correct: 0,
    total: 0
};

let currentConfig = {
    position: null,
    action: null,
    stackDepth: null,
    availableActions: []
};

let currentHand = null;

// DOM elements
const configScreen = document.getElementById('config-screen');
const practiceScreen = document.getElementById('practice-screen');
const positionSelect = document.getElementById('position');
const actionSelect = document.getElementById('action');
const stackDepthSelect = document.getElementById('stack-depth');
const startBtn = document.getElementById('start-btn');
const currentHandDisplay = document.getElementById('current-hand');
const configDisplay = document.getElementById('config-display');
const buttonGroup = document.querySelector('.button-group'); // Container for buttons
const backBtn = document.getElementById('back-btn');
const nextBtn = document.getElementById('next-btn');
const feedbackDiv = document.getElementById('feedback');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadPositions();
    setupEventListeners();
});

function setupEventListeners() {
    positionSelect.addEventListener('change', onPositionChange);
    actionSelect.addEventListener('change', onActionChange);
    stackDepthSelect.addEventListener('change', onStackDepthChange);
    startBtn.addEventListener('click', startPractice);
    // Dynamic buttons handle their own events
    nextBtn.addEventListener('click', loadNextHand);
    backBtn.addEventListener('click', backToMenu);
}

async function loadPositions() {
    try {
        const response = await fetch('/api/positions');
        const positions = await response.json();

        positions.forEach(pos => {
            const option = document.createElement('option');
            option.value = pos;
            option.textContent = pos;
            positionSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading positions:', error);
    }
}

async function onPositionChange() {
    const position = positionSelect.value;

    // Reset dependent selects
    actionSelect.innerHTML = '<option value="">Choose action...</option>';
    stackDepthSelect.innerHTML = '<option value="">Choose stack depth...</option>';
    actionSelect.disabled = !position;
    stackDepthSelect.disabled = true;
    startBtn.disabled = true;

    if (!position) return;

    try {
        const response = await fetch(`/api/actions/${position}`);
        const actions = await response.json();

        actions.forEach(action => {
            const option = document.createElement('option');
            option.value = action;
            option.textContent = action;
            actionSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading actions:', error);
    }
}

async function onActionChange() {
    const position = positionSelect.value;
    const action = actionSelect.value;

    stackDepthSelect.innerHTML = '<option value="">Choose stack depth...</option>';
    stackDepthSelect.disabled = !action;
    startBtn.disabled = true;

    if (!action) return;

    try {
        const response = await fetch(`/api/stack-depths/${position}/${action}`);
        const stackDepths = await response.json();

        stackDepths.forEach(depth => {
            const option = document.createElement('option');
            option.value = depth;
            option.textContent = depth;
            stackDepthSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading stack depths:', error);
    }
}

function onStackDepthChange() {
    const stackDepth = stackDepthSelect.value;
    startBtn.disabled = !stackDepth;
}

async function startPractice() {
    currentConfig.position = positionSelect.value;
    currentConfig.action = actionSelect.value;
    currentConfig.stackDepth = stackDepthSelect.value;

    try {
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                position: currentConfig.position,
                action: currentConfig.action,
                stack_depth: currentConfig.stackDepth
            })
        });

        const data = await response.json();

        if (data.success) {
            configDisplay.textContent = `${currentConfig.position} - ${currentConfig.action} - ${currentConfig.stackDepth} (${data.range_size} hands)`;
            currentConfig.availableActions = data.available_actions || ['in_range'];

            setupActionButtons();

            configScreen.classList.remove('active');
            practiceScreen.classList.add('active');
            loadNextHand();
        }
    } catch (error) {
        console.error('Error starting practice:', error);
    }
}

const ACTION_COLORS = {
    'in_range': '#28a745', // Green
    'open': '#28a745',     // Green
    '3bet': '#d9534f',     // Red
    '4bet': '#d9534f',     // Red
    'call': '#5bc0de',     // Blue
    'limp': '#f0ad4e',     // Orange/Yellow
    'check': '#f0ad4e',    // Orange
    'raise': '#d9534f',    // Red
    'fold': '#dc3545',     // Red (Danger)
    'default': '#6c757d'   // Grey
};

function getActionColor(action) {
    // Handle variants like '3bet_l', 'raise_l' -> map to base color
    let base = action.split('_')[0];
    return ACTION_COLORS[base] || ACTION_COLORS[action] || ACTION_COLORS['default'];
}

function getActionLabel(action) {
    if (action === 'in_range') return '✓ In Range';
    if (action === 'fold') return '✗ Fold';
    // Capitalize and replace underscore
    return action.charAt(0).toUpperCase() + action.slice(1).replace('_', ' ');
}

function setupActionButtons() {
    buttonGroup.innerHTML = ''; // Clear existing

    const actions = [...currentConfig.availableActions];

    // Create buttons for active actions
    actions.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'btn btn-large action-btn';
        btn.textContent = getActionLabel(action);

        const color = getActionColor(action);
        btn.style.backgroundColor = color;
        btn.style.color = 'white';

        btn.dataset.action = action;
        btn.addEventListener('click', () => submitAnswer(action));
        buttonGroup.appendChild(btn);
    });

    // Always add Fold button last
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

    // Enable all action buttons
    const btns = document.querySelectorAll('.action-btn');
    btns.forEach(btn => btn.disabled = false);

    // Reset styles (opacity, border, etc)
    btns.forEach(btn => {
        btn.style.opacity = '1';
        btn.style.transform = 'none';
        btn.style.boxShadow = 'none';
        btn.style.border = 'none';

        // Reset label (remove checkmark if added)
        const action = btn.dataset.action;
        btn.textContent = getActionLabel(action);
        // Re-apply explicit fold label if needed, but getActionLabel handles it
        if (action === 'fold') btn.textContent = '✗ Fold';
    });

    try {
        const response = await fetch('/api/next-hand');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        currentHand = data.hand;
        currentHandDisplay.textContent = currentHand;

    } catch (error) {
        console.error('Error loading next hand:', error);
    }
}

async function submitAnswer(action) {
    // Disable buttons
    const btns = document.querySelectorAll('.action-btn');
    btns.forEach(btn => btn.disabled = true);

    console.log('Submitting answer:', { hand: currentHand, action: action });

    try {
        const response = await fetch('/api/check-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hand: currentHand,
                action: action
            })
        });

        const data = await response.json();
        console.log('Server response:', data);

        // Update stats
        stats.total++;
        if (data.correct) {
            stats.correct++;
        }
        updateStats();

        // Show feedback
        showFeedback(data);

        // Show Next button
        nextBtn.style.display = 'block';
    } catch (error) {
        console.error('Error checking answer:', error);
    }
}

function showFeedback(data) {
    feedbackDiv.classList.remove('hidden', 'correct', 'incorrect');

    // Highlight the correct action button
    const actualAction = data.actual_action;
    const correctBtn = document.querySelector(`.action-btn[data-action="${actualAction}"]`);
    if (correctBtn) {
        // Make it stand out
        correctBtn.style.opacity = '1';
        correctBtn.style.transform = 'scale(1.05)';
        correctBtn.style.boxShadow = '0 0 15px rgba(255, 215, 0, 0.7)'; // Gold glow
        correctBtn.style.border = '3px solid white';

        // Add checkmark if not present
        if (!correctBtn.textContent.includes('✓') && !correctBtn.textContent.includes('✗')) {
            correctBtn.textContent = '✓ ' + correctBtn.textContent;
        }
    }

    // Dim other buttons (including the one user picked if wrong)
    const allBtns = document.querySelectorAll('.action-btn');
    allBtns.forEach(btn => {
        if (btn !== correctBtn) {
            btn.style.opacity = '0.5';
        }
    });

    if (data.correct) {
        feedbackDiv.classList.add('correct');
        let html = '<div class="feedback-title">✓ CORRECT!</div>';

        if (data.user_action === "fold") {
            html += `<div class="feedback-detail">Correct fold.</div>`;
        } else {
            html += `<div class="feedback-detail">Yes, it is ${data.user_action}.</div>`;
        }

        // Show bottom of range if available
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
    document.getElementById('correct').textContent = stats.correct;
    document.getElementById('total').textContent = stats.total;

    const accuracy = stats.total > 0 ? ((stats.correct / stats.total) * 100).toFixed(1) : 0;
    document.getElementById('accuracy').textContent = accuracy + '%';
}

function backToMenu() {
    practiceScreen.classList.remove('active');
    configScreen.classList.add('active');
    feedbackDiv.classList.add('hidden');
    nextBtn.style.display = 'none';
}
