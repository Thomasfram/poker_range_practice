// ─────────────────────────────────────────────
//  FLOP PAGE — Configuration & Table UI
// ─────────────────────────────────────────────

const POSITIONS = ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'];

const STACK_DEPTHS = [
    { label: '15bb', value: 15, desc: 'Short stack' },
    { label: '25bb', value: 25, desc: 'Short-mid' },
    { label: '40bb', value: 40, desc: 'Mid stack' },
    { label: '50bb', value: 50, desc: 'Standard' },
    { label: '100bb', value: 100, desc: 'Deep stack' },
];

const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'];
const SUITS = ['♠', '♥', '♦', '♣'];
const RED_SUITS = new Set(['♥', '♦']);

// State
const flopState = {
    hero: null,
    villain: null,
    stackDepth: null,
};

const flopPractice = {
    heroHand: [],
    communityCards: [],
    stats: { correct: 0, total: 0 },
};

// ─── Boot ────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initFlopConfig();
    initFlopNavigation();
});

// ─── Tab Navigation ──────────────────────────

function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    const pages = document.querySelectorAll('.page');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.dataset.page;
            tabs.forEach(t => t.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`page-${target}`).classList.add('active');
        });
    });
}

// ─── Config UI ───────────────────────────────

function initFlopConfig() {
    renderPositionButtons('hero-position-buttons', 'hero');
    renderPositionButtons('villain-position-buttons', 'villain');
    renderStackDepthButtons();
}

function renderPositionButtons(containerId, role) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    POSITIONS.forEach(pos => {
        const btn = document.createElement('button');
        btn.className = 'position-btn';
        btn.textContent = pos;
        btn.dataset.position = pos;
        btn.addEventListener('click', () => selectPosition(role, pos));
        container.appendChild(btn);
    });
}

function renderStackDepthButtons() {
    const container = document.getElementById('flop-stack-depth-buttons');
    if (!container) return;
    container.innerHTML = '';
    STACK_DEPTHS.forEach(sd => {
        const btn = document.createElement('button');
        btn.className = 'stack-depth-btn';
        btn.innerHTML = `<span class="sd-label">${sd.label}</span><span class="sd-desc">${sd.desc}</span>`;
        btn.dataset.value = sd.value;
        btn.addEventListener('click', () => selectStackDepth(sd));
        container.appendChild(btn);
    });
}

function selectPosition(role, position) {
    flopState[role] = position;
    const id = role === 'hero' ? 'hero-position-buttons' : 'villain-position-buttons';
    document.querySelectorAll(`#${id} .position-btn`).forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.position === position);
    });
    validatePositionConflict();
    updateFlopSummary();
    updateFlopStartBtn();
}

function selectStackDepth(sd) {
    flopState.stackDepth = sd;
    document.querySelectorAll('.stack-depth-btn').forEach(btn => {
        btn.classList.toggle('selected', parseInt(btn.dataset.value) === sd.value);
    });
    const preview = document.getElementById('stack-depth-preview');
    if (preview) {
        preview.textContent = `${sd.label} — ${sd.desc}`;
        preview.classList.add('has-value');
    }
    updateFlopSummary();
    updateFlopStartBtn();
}

function validatePositionConflict() {
    ['hero-position-buttons', 'villain-position-buttons'].forEach(id => {
        document.querySelectorAll(`#${id} .position-btn`).forEach(b => b.classList.remove('conflict'));
    });
    if (flopState.hero && flopState.villain && flopState.hero === flopState.villain) {
        ['hero-position-buttons', 'villain-position-buttons'].forEach(id => {
            document.querySelectorAll(`#${id} .position-btn.selected`).forEach(b => b.classList.add('conflict'));
        });
    }
}

function updateFlopSummary() {
    const el = document.getElementById('flop-summary-text');
    if (!el) return;
    const { hero, villain, stackDepth } = flopState;
    if (hero && villain && hero === villain) {
        el.innerHTML = `<span class="summary-error">⚠ Hero and Villain cannot be the same position.</span>`;
        return;
    }
    const parts = [];
    if (hero) parts.push(`<span class="summary-chip hero-chip">Hero: <strong>${hero}</strong></span>`);
    if (villain) parts.push(`<span class="summary-chip villain-chip">Villain: <strong>${villain}</strong></span>`);
    if (stackDepth) parts.push(`<span class="summary-chip stack-chip">Stack: <strong>${stackDepth.label}</strong></span>`);
    el.innerHTML = parts.length ? parts.join(' vs ') : 'Complete the configuration above to start.';
}

function updateFlopStartBtn() {
    const btn = document.getElementById('flop-start-btn');
    if (!btn) return;
    const { hero, villain, stackDepth } = flopState;
    btn.disabled = !hero || !villain || !stackDepth || hero === villain;
}

// ─── Navigation ──────────────────────────────

function initFlopNavigation() {
    const startBtn = document.getElementById('flop-start-btn');
    const backBtn = document.getElementById('flop-back-btn');
    const configScr = document.getElementById('flop-config-screen');
    const practiceScr = document.getElementById('flop-practice-screen');

    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (startBtn.disabled) return;
            startFlopPractice(configScr, practiceScr);
        });
    }
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            practiceScr.classList.remove('active');
            configScr.classList.add('active');
        });
    }

    const nextBtn = document.getElementById('flop-next-btn');
    if (nextBtn) nextBtn.addEventListener('click', dealFlopHand);
}

// ─── Practice Session ─────────────────────────

function startFlopPractice(configScr, practiceScr) {
    const { hero, villain, stackDepth } = flopState;

    // Update labels
    document.getElementById('flop-config-display').textContent =
        `${hero} vs ${villain} — ${stackDepth.label}`;
    document.getElementById('hero-pos-label').textContent = hero;
    document.getElementById('villain-pos-label').textContent = villain;

    // Reset stats
    flopPractice.stats = { correct: 0, total: 0 };
    updateFlopStats();

    // Build action buttons (placeholder for now — bet/check/fold)
    buildActionButtons();

    configScr.classList.remove('active');
    practiceScr.classList.add('active');

    dealFlopHand();
}

// ─── Card Generation ─────────────────────────

function buildDeck() {
    const deck = [];
    for (const rank of RANKS) {
        for (const suit of SUITS) {
            deck.push({ rank, suit });
        }
    }
    return deck;
}

function shuffle(arr) {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
}

function dealFlopHand() {
    const deck = shuffle(buildDeck());
    let i = 0;

    // Hero gets 2 cards
    flopPractice.heroHand = [deck[i++], deck[i++]];
    // Skip 2 for villain (face down)
    i += 2;
    // Burn 1
    i++;
    // Flop 3
    flopPractice.communityCards = [deck[i++], deck[i++], deck[i++]];

    renderHeroCards();
    renderCommunityCards();
    resetActionArea();
}

// ─── Rendering ───────────────────────────────

function cardRankDisplay(rank) {
    return rank === 'T' ? '10' : rank;
}

function renderHeroCards() {
    const cards = flopPractice.heroHand;
    ['hero-card-1', 'hero-card-2'].forEach((id, idx) => {
        const el = document.getElementById(id);
        const card = cards[idx];
        if (!el || !card) return;

        const isRed = RED_SUITS.has(card.suit);
        el.className = `card hero-card deal-anim${isRed ? ' red-suit' : ''}`;
        el.style.animationDelay = `${idx * 0.1}s`;
        el.style.color = isRed ? '#d32f2f' : '#111';
        el.innerHTML = `
            <span class="card-rank">${cardRankDisplay(card.rank)}</span>
            <span class="card-suit-icon">${card.suit}</span>
        `;
    });
}

function renderCommunityCards() {
    const cards = flopPractice.communityCards;
    ['flop-c1', 'flop-c2', 'flop-c3'].forEach((id, idx) => {
        const el = document.getElementById(id);
        const card = cards[idx];
        if (!el || !card) return;

        const isRed = RED_SUITS.has(card.suit);
        el.className = `card community-card revealed deal-anim`;
        el.style.animationDelay = `${(idx + 2) * 0.1}s`;
        el.style.color = isRed ? '#d32f2f' : '#111';
        el.innerHTML = `
            <span style="font-size:0.85rem;font-weight:800;line-height:1.1">${cardRankDisplay(card.rank)}</span>
            <span style="font-size:1rem;line-height:1">${card.suit}</span>
        `;
    });
}

// ─── Action Buttons ───────────────────────────

// Placeholder actions — will be replaced with strategy logic later
const FLOP_ACTIONS = [
    { id: 'bet', label: 'Bet', color: '#e67e22' },
    { id: 'check', label: 'Check', color: '#27ae60' },
    { id: 'fold', label: 'Fold', color: '#c0392b' },
];

function buildActionButtons() {
    const group = document.getElementById('flop-btn-group');
    if (!group) return;
    group.innerHTML = '';

    FLOP_ACTIONS.forEach(action => {
        const btn = document.createElement('button');
        btn.className = 'flop-action-btn';
        btn.textContent = action.label;
        btn.dataset.action = action.id;
        btn.style.backgroundColor = action.color;
        btn.addEventListener('click', () => submitFlopAnswer(action.id));
        group.appendChild(btn);
    });
}

function resetActionArea() {
    const feedback = document.getElementById('flop-feedback');
    const nextBtn = document.getElementById('flop-next-btn');
    if (feedback) { feedback.classList.add('hidden'); feedback.className = 'feedback hidden'; }
    if (nextBtn) nextBtn.style.display = 'none';

    document.querySelectorAll('.flop-action-btn').forEach(btn => {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.transform = '';
        btn.style.boxShadow = '';
    });

    document.getElementById('flop-situation').textContent = 'What is your action?';
}

// Placeholder answer logic — always shows "coming soon" for strategy
function submitFlopAnswer(action) {
    document.querySelectorAll('.flop-action-btn').forEach(btn => btn.disabled = true);

    const feedback = document.getElementById('flop-feedback');
    const nextBtn = document.getElementById('flop-next-btn');

    // Placeholder: strategy not yet defined — just acknowledge + show next
    feedback.classList.remove('hidden', 'correct', 'incorrect');
    feedback.classList.add('correct');
    feedback.innerHTML = `
        <div class="feedback-title">Hand dealt!</div>
        <div class="feedback-detail">
            Strategy logic coming soon. You selected: <strong>${action}</strong>
        </div>
    `;

    flopPractice.stats.total++;
    updateFlopStats();

    if (nextBtn) nextBtn.style.display = 'block';
}

function updateFlopStats() {
    const { correct, total } = flopPractice.stats;
    const acc = total > 0 ? ((correct / total) * 100).toFixed(0) : 0;
    const cEl = document.getElementById('flop-correct');
    const tEl = document.getElementById('flop-total');
    const aEl = document.getElementById('flop-accuracy');
    if (cEl) cEl.textContent = correct;
    if (tEl) tEl.textContent = total;
    if (aEl) aEl.textContent = acc + '%';
}