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

async function dealFlopHand() {
    const { hero, villain, stackDepth } = flopState;

    try {
        // 1. Demander une main IN RANGE au backend
        const res = await fetch('/api/flop/hero-hand', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ hero, villain, stackDepth: stackDepth.value })
        });
        const data = await res.json();
        const abstractHand = data.hand; // ex: "AKs", "77", "T9o"

        // 2. Générer un paquet neuf
        let deck = buildDeck();

        // 3. Extraire les cartes réelles correspondantes et les retirer du paquet
        flopPractice.heroHand = extractCardsForHand(abstractHand, deck);

        // 4. Mélanger le paquet restant
        deck = shuffle(deck);

        let i = 0;
        // On passe 2 cartes face cachée pour le villain
        i += 2;
        // On brûle 1 carte
        i++;
        // On tire le Flop
        flopPractice.communityCards = [deck[i++], deck[i++], deck[i++]];

        renderHeroCards();
        renderCommunityCards();
        resetActionArea();

    } catch (error) {
        console.error("Erreur lors de la distribution du flop:", error);
    }
}

function extractCardsForHand(handStr, deck) {
    // Analyse la main (ex: "AKs" -> rank1="A", rank2="K", type="s")
    const rank1 = handStr[0];
    const rank2 = handStr[1];
    const type = handStr.length > 2 ? handStr[2] : 'pair';

    let c1, c2;

    if (type === 'pair') {
        // Paire : on trouve toutes les cartes de ce rang et on en prend 2 au hasard
        const options = deck.filter(c => c.rank === rank1);
        const picked = shuffle(options).slice(0, 2);
        c1 = picked[0];
        c2 = picked[1];
    } else if (type === 's') {
        // Suited : on choisit 1 couleur au hasard, et on prend les deux cartes
        const suits = ['♠', '♥', '♦', '♣'];
        const suit = suits[Math.floor(Math.random() * suits.length)];
        c1 = deck.find(c => c.rank === rank1 && c.suit === suit);
        c2 = deck.find(c => c.rank === rank2 && c.suit === suit);
    } else if (type === 'o') {
        // Offsuit : on choisit 2 couleurs différentes au hasard
        const suits = ['♠', '♥', '♦', '♣'];
        const suit1 = suits[Math.floor(Math.random() * suits.length)];
        let suit2 = suits[Math.floor(Math.random() * suits.length)];
        while (suit1 === suit2) {
            suit2 = suits[Math.floor(Math.random() * suits.length)];
        }
        c1 = deck.find(c => c.rank === rank1 && c.suit === suit1);
        c2 = deck.find(c => c.rank === rank2 && c.suit === suit2);
    }

    // Retirer physiquement les cartes du deck
    deck.splice(deck.findIndex(c => c === c1), 1);
    deck.splice(deck.findIndex(c => c === c2), 1);

    return [c1, c2];
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

// State for current turn's pending action
const flopTurn = {
    pendingAction: null,  // 'bet' | 'check'
};

function buildActionButtons() {
    const group = document.getElementById('flop-btn-group');
    if (!group) return;
    group.innerHTML = '';
    flopTurn.pendingAction = null;

    const betBtn = makeActionBtn('Bet', '#e67e22', () => selectCbetAction('bet'));
    const checkBtn = makeActionBtn('Check', '#27ae60', () => selectCbetAction('check'));
    group.appendChild(betBtn);
    group.appendChild(checkBtn);
}

function makeActionBtn(label, color, onClick) {
    const btn = document.createElement('button');
    btn.className = 'flop-action-btn';
    btn.textContent = label;
    btn.style.backgroundColor = color;
    btn.addEventListener('click', onClick);
    return btn;
}

function selectCbetAction(action) {
    flopTurn.pendingAction = action;

    // Highlight selected button
    document.querySelectorAll('.flop-action-btn').forEach(btn => {
        btn.style.opacity = btn.textContent.toLowerCase() === action ? '1' : '0.4';
    });

    if (action === 'bet') {
        showSizingButtons();
    } else {
        // Check: submit immediately
        submitCbet('check', null);
    }
}

const SIZINGS = [25, 33, 50, 66];

function showSizingButtons() {
    const group = document.getElementById('flop-btn-group');
    // Keep bet/check row, add sizing row below
    const existingRow = group.querySelector('.sizing-row');
    if (existingRow) existingRow.remove();

    const row = document.createElement('div');
    row.className = 'sizing-row';
    row.style.cssText = 'display:flex;gap:8px;justify-content:center;margin-top:8px;flex-wrap:wrap;';

    SIZINGS.forEach(pct => {
        const btn = document.createElement('button');
        btn.className = 'flop-action-btn sizing-btn';
        btn.textContent = `${pct}%`;
        btn.style.cssText = 'background:#2980b9;min-width:70px;padding:8px 14px;font-size:0.9rem;';
        btn.addEventListener('click', () => submitCbet('bet', pct));
        row.appendChild(btn);
    });

    group.appendChild(row);
    document.getElementById('flop-situation').textContent = 'Choisissez le sizing :';
}

async function submitCbet(action, sizing) {
    document.querySelectorAll('.flop-action-btn').forEach(btn => btn.disabled = true);

    const { hero, villain, stackDepth } = flopState;

    const payload = {
        hero_cards: flopPractice.heroHand.map(c => ({ rank: c.rank, suit: c.suit })),
        board_cards: flopPractice.communityCards.map(c => ({ rank: c.rank, suit: c.suit })),
        hero_position: hero,
        villain_position: villain,
        stack_depth: stackDepth.value,
        user_action: action,
        user_sizing: sizing,
    };

    // Only BTN/CO vs BB is supported for now
    if (!['BTN', 'CO'].includes(hero) || villain !== 'BB') {
        document.getElementById('flop-feedback').className = 'feedback correct';
        document.getElementById('flop-feedback').innerHTML = `
            <div class="feedback-title">Situation non supportée</div>
            <div class="feedback-detail">La stratégie Cbet est implémentée uniquement pour BTN/CO vs BB pour l'instant.</div>
        `;
        flopPractice.stats.total++;
        updateFlopStats();
        document.getElementById('flop-next-btn').style.display = 'block';
        return;
    }

    try {
        const res = await fetch('/api/flop/check-cbet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || 'Erreur serveur');
        }
        showCbetFeedback(data, action, sizing);
    } catch (err) {
        console.error('check-cbet error:', err);
        document.getElementById('flop-feedback').className = 'feedback incorrect';
        document.getElementById('flop-feedback').innerHTML = `<div class="feedback-title">Erreur : ${err.message}</div>`;
        document.getElementById('flop-next-btn').style.display = 'block';
    }
}

function showCbetFeedback(data, userAction, userSizing) {
    const feedback = document.getElementById('flop-feedback');
    const nextBtn = document.getElementById('flop-next-btn');

    const isCorrect = data.correct;
    feedback.className = `feedback ${isCorrect ? 'correct' : 'incorrect'}`;

    const textureColors = {
        TRES_DRY: '#27ae60',
        INTERMEDIAIRE: '#e67e22',
        DRAWY: '#c0392b',
    };
    const tc = textureColors[data.texture] || '#888';

    const textureBadge = `<span style="background:${tc};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.8rem;font-weight:700;">${data.texture_label}</span>`;

    let actionLine;
    if (data.correct_action === 'bet') {
        actionLine = `Cbet <strong>${data.correct_sizing}%</strong> du pot`;
    } else {
        actionLine = `Check`;
    }

    let userLine;
    if (userAction === 'bet' && userSizing) {
        userLine = `Vous avez joué : <strong>Bet ${userSizing}%</strong>`;
    } else {
        userLine = `Vous avez joué : <strong>${userAction === 'bet' ? 'Bet' : 'Check'}</strong>`;
    }

    feedback.innerHTML = `
        <div class="feedback-title">${isCorrect ? '✓ Correct !' : '✗ Incorrect'}</div>
        <div class="feedback-detail" style="margin-top:6px;">
            Board : ${textureBadge} — Cbet ${data.cbet_frequency}
        </div>
        <div class="feedback-detail" style="margin-top:4px;">
            Ta main : <em>${data.hand_label}</em>
        </div>
        <div class="feedback-detail" style="margin-top:4px;">
            ${isCorrect ? '' : `Bonne réponse : <strong>${actionLine}</strong><br>`}${userLine}
        </div>
    `;

    if (isCorrect) {
        flopPractice.stats.correct++;
    }
    flopPractice.stats.total++;
    updateFlopStats();

    if (nextBtn) nextBtn.style.display = 'block';
}

function resetActionArea() {
    const feedback = document.getElementById('flop-feedback');
    const nextBtn = document.getElementById('flop-next-btn');
    if (feedback) feedback.className = 'feedback hidden';
    if (nextBtn) nextBtn.style.display = 'none';

    buildActionButtons();
    document.getElementById('flop-situation').textContent = 'Bet ou Check ?';
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