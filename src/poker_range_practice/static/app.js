// Global state
let stats = {
    correct: 0,
    total: 0
};

let currentConfig = {
    position: null,
    action: null,
    stackDepth: null
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
const inRangeBtn = document.getElementById('in-range-btn');
const foldBtn = document.getElementById('fold-btn');
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
    inRangeBtn.addEventListener('click', () => submitAnswer(true));
    foldBtn.addEventListener('click', () => submitAnswer(false));
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
            configScreen.classList.remove('active');
            practiceScreen.classList.add('active');
            loadNextHand();
        }
    } catch (error) {
        console.error('Error starting practice:', error);
    }
}

async function loadNextHand() {
    feedbackDiv.classList.add('hidden');
    nextBtn.style.display = 'none';
    inRangeBtn.disabled = true;
    foldBtn.disabled = true;

    try {
        const response = await fetch('/api/next-hand');
        const data = await response.json();

        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        currentHand = data.hand;
        currentHandDisplay.textContent = currentHand;

        inRangeBtn.disabled = false;
        foldBtn.disabled = false;
    } catch (error) {
        console.error('Error loading next hand:', error);
    }
}

async function submitAnswer(inRange) {
    inRangeBtn.disabled = true;
    foldBtn.disabled = true;

    console.log('Submitting answer:', { hand: currentHand, in_range: inRange });

    try {
        const response = await fetch('/api/check-answer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                hand: currentHand,
                in_range: inRange
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

    if (data.correct) {
        feedbackDiv.classList.add('correct');
        let html = '<div class="feedback-title">✓ CORRECT!</div>';

        // Show bottom of range if available
        if (data.bottom_of_range) {
            html += `<div class="feedback-detail">Bottom of range: <strong>${data.bottom_of_range}</strong></div>`;
        }

        feedbackDiv.innerHTML = html;
    } else {
        feedbackDiv.classList.add('incorrect');
        let html = '<div class="feedback-title">✗ INCORRECT</div>';

        if (data.actually_in_range) {
            html += `<div class="feedback-detail">${currentHand} IS in range</div>`;
        } else {
            html += `<div class="feedback-detail">${currentHand} is NOT in range (fold)</div>`;
            if (data.closest_hand) {
                html += `<div class="feedback-detail">Closest hand in range: <strong>${data.closest_hand}</strong></div>`;
            }
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
