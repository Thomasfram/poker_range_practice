// ─────────────────────────────────────────────
//  FLOP PAGE — Configuration & Table UI
// ─────────────────────────────────────────────

const POSITIONS = ['CO', 'BTN', 'SB', 'BB'];

const STACK_DEPTHS = [
    { label: '20bb', value: 20, desc: 'Short stack' },
    { label: '50bb', value: 50, desc: 'Standard' },
    { label: '100bb', value: 100, desc: 'Deep stack' },
];

const RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'];
const SUITS = ['♠', '♥', '♦', '♣'];
const RED_SUITS = new Set(['♥', '♦']);

// All valid (hero, villain) flop situations
const FLOP_EVAL_SITUATIONS = [
    { key: 'BTN/BB', label: 'BTN vs BB', hero: 'BTN', villain: 'BB', type: 'cbet' },
    { key: 'BTN/SB', label: 'BTN vs SB', hero: 'BTN', villain: 'SB', type: 'cbet' },
    { key: 'CO/BB',  label: 'CO vs BB',  hero: 'CO',  villain: 'BB', type: 'cbet' },
    { key: 'BB/BTN', label: 'BB vs BTN', hero: 'BB',  villain: 'BTN', type: 'defense' },
    { key: 'BB/CO',  label: 'BB vs CO',  hero: 'BB',  villain: 'CO',  type: 'defense' },
    { key: 'SB/BB',      label: 'BvB: SB Raise vs BB', hero: 'SB', villain: 'BB', type: 'cbet', scenario: 'raise' },
    { key: 'SB/BB_limp', label: 'BvB: SB Limp vs BB',  hero: 'SB', villain: 'BB', type: 'cbet', scenario: 'limp'  },
];

// State
const flopState = {
    hero: null,
    villain: null,
    stackDepth: null,
    scenario: null,   // 'raise' | 'limp' | null (only relevant for SB vs BB)
};

const flopPractice = {
    heroHand: [],
    villainHand: [],
    communityCards: [],
    stats: { correct: 0, total: 0 },
};

let flopGuideMode = false;

// Eval mode state
const flopEval = {
    active: false,
    situations: new Set(),  // Set of situation keys e.g. 'BTN/BB'
    depths: new Set(),      // Set of stack depth values (numbers)
    handCount: 20,
    handsDone: 0,
    results: {},  // key -> { correct, total, hero, villain, stackDepth, label }
};

// ─── Boot ────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initFlopConfig();
    initFlopNavigation();
    initFlopEvalConfig();
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
    renderBvBScenarioButtons();
}

function renderBvBScenarioButtons() {
    const container = document.getElementById('bvb-scenario-buttons');
    if (!container) return;
    container.innerHTML = '';
    [{ key: 'raise', label: 'SB Raise' }, { key: 'limp', label: 'SB Limp' }].forEach(({ key, label }) => {
        const btn = document.createElement('button');
        btn.className = 'position-btn';
        btn.textContent = label;
        btn.dataset.scenario = key;
        btn.addEventListener('click', () => selectBvBScenario(key));
        container.appendChild(btn);
    });
}

function selectBvBScenario(scenario) {
    flopState.scenario = scenario;
    document.querySelectorAll('#bvb-scenario-buttons .position-btn').forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.scenario === scenario);
    });
    updateFlopSummary();
    updateFlopStartBtn();
}

function updateBvBScenarioVisibility() {
    const isBvB = flopState.hero === 'SB' && flopState.villain === 'BB';
    const group = document.getElementById('bvb-scenario-group');
    if (group) group.style.display = isBvB ? '' : 'none';
    if (!isBvB) {
        flopState.scenario = null;
        document.querySelectorAll('#bvb-scenario-buttons .position-btn').forEach(b => b.classList.remove('selected'));
    }
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
    updateBvBScenarioVisibility();
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
    const isBvB = hero === 'SB' && villain === 'BB';
    if (isBvB && flopState.scenario) parts.push(`<span class="summary-chip stack-chip">Scénario: <strong>${flopState.scenario === 'limp' ? 'SB Limp' : 'SB Raise'}</strong></span>`);
    el.innerHTML = parts.length ? parts.join(' vs ') : 'Complete the configuration above to start.';
}

function updateFlopStartBtn() {
    const btn = document.getElementById('flop-start-btn');
    if (!btn) return;
    if (flopGuideMode) {
        btn.textContent = 'Voir le Guide →';
        const { hero, villain, stackDepth, scenario } = flopState;
        const needsScenario = hero === 'SB' && villain === 'BB';
        btn.disabled = !hero || !villain || !stackDepth || hero === villain || (needsScenario && !scenario);
        return;
    }
    btn.textContent = 'Start Flop Practice';
    if (flopEval.active) {
        btn.disabled = flopEval.situations.size === 0 || flopEval.depths.size === 0;
    } else {
        const { hero, villain, stackDepth, scenario } = flopState;
        const needsScenario = hero === 'SB' && villain === 'BB';
        btn.disabled = !hero || !villain || !stackDepth || hero === villain || (needsScenario && !scenario);
    }
}

// ─── Eval Config ─────────────────────────────

function initFlopEvalConfig() {
    document.getElementById('flop-mode-classic').addEventListener('click', () => setFlopMode(false));
    document.getElementById('flop-mode-eval').addEventListener('click',   () => setFlopMode(true));
    document.getElementById('flop-mode-guide').addEventListener('click',  () => setFlopGuideMode());

    // Situation toggle buttons
    const sitContainer = document.getElementById('flop-eval-situations');
    FLOP_EVAL_SITUATIONS.forEach(sit => {
        const btn = document.createElement('button');
        btn.className = 'eval-toggle-btn';
        btn.innerHTML = `${sit.label} <span class="sit-type-badge">${sit.type === 'cbet' ? 'cbet' : 'défense'}</span>`;
        btn.dataset.key = sit.key;
        btn.addEventListener('click', () => {
            if (flopEval.situations.has(sit.key)) {
                flopEval.situations.delete(sit.key);
                btn.classList.remove('selected');
            } else {
                flopEval.situations.add(sit.key);
                btn.classList.add('selected');
            }
            updateFlopStartBtn();
        });
        sitContainer.appendChild(btn);
    });

    // Stack depth toggle buttons
    const depthContainer = document.getElementById('flop-eval-depths');
    STACK_DEPTHS.forEach(sd => {
        const btn = document.createElement('button');
        btn.className = 'eval-toggle-btn';
        btn.textContent = sd.label;
        btn.dataset.value = sd.value;
        btn.addEventListener('click', () => {
            if (flopEval.depths.has(sd.value)) {
                flopEval.depths.delete(sd.value);
                btn.classList.remove('selected');
            } else {
                flopEval.depths.add(sd.value);
                btn.classList.add('selected');
            }
            updateFlopStartBtn();
        });
        depthContainer.appendChild(btn);
    });

    document.getElementById('flop-eval-count-input').addEventListener('input', e => {
        const v = parseInt(e.target.value, 10);
        if (v > 0) flopEval.handCount = v;
    });
}

function setFlopMode(evalMode) {
    flopEval.active = evalMode;
    flopGuideMode = false;
    document.getElementById('flop-mode-classic').classList.toggle('active', !evalMode);
    document.getElementById('flop-mode-eval').classList.toggle('active', evalMode);
    document.getElementById('flop-mode-guide').classList.remove('active');
    document.getElementById('flop-classic-config').style.display = evalMode ? 'none' : '';
    document.getElementById('flop-eval-config').style.display    = evalMode ? '' : 'none';

    // Reset eval state
    flopEval.situations.clear();
    flopEval.depths.clear();
    flopEval.handsDone = 0;
    flopEval.results = {};
    document.querySelectorAll('#flop-eval-situations .eval-toggle-btn, #flop-eval-depths .eval-toggle-btn').forEach(b => b.classList.remove('selected'));

    updateFlopStartBtn();
}

function setFlopGuideMode() {
    flopEval.active = false;
    flopGuideMode = true;
    document.getElementById('flop-mode-classic').classList.remove('active');
    document.getElementById('flop-mode-eval').classList.remove('active');
    document.getElementById('flop-mode-guide').classList.add('active');
    document.getElementById('flop-classic-config').style.display = '';
    document.getElementById('flop-eval-config').style.display = 'none';
    updateFlopStartBtn();
}

// ─── Navigation ──────────────────────────────

function initFlopNavigation() {
    const startBtn  = document.getElementById('flop-start-btn');
    const backBtn   = document.getElementById('flop-back-btn');
    const configScr = document.getElementById('flop-config-screen');
    const practiceScr = document.getElementById('flop-practice-screen');

    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (startBtn.disabled) return;
            if (flopGuideMode) {
                showFlopGuide(configScr);
            } else if (flopEval.active) {
                startFlopEvalSession(configScr, practiceScr);
            } else {
                startFlopPractice(configScr, practiceScr);
            }
        });
    }
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            practiceScr.classList.remove('active');
            configScr.classList.add('active');
            document.getElementById('flop-eval-progress').classList.add('hidden');
        });
    }

    const guideBk = document.getElementById('guide-back-btn');
    if (guideBk) {
        guideBk.addEventListener('click', () => {
            document.getElementById('flop-guide-screen').classList.remove('active');
            configScr.classList.add('active');
        });
    }

    const nextBtn = document.getElementById('flop-next-btn');
    if (nextBtn) nextBtn.onclick = dealFlopHand;

    document.getElementById('flop-results-back-btn').addEventListener('click', flopResultsBackToMenu);
    document.getElementById('flop-results-retry-btn').addEventListener('click', flopResultsRetry);
}

// ─── Eval Session ────────────────────────────

function startFlopEvalSession(configScr, practiceScr) {
    flopEval.handsDone = 0;
    flopEval.results = {};
    flopPractice.stats = { correct: 0, total: 0 };
    updateFlopStats();

    configScr.classList.remove('active');
    practiceScr.classList.add('active');

    const progress = document.getElementById('flop-eval-progress');
    progress.classList.remove('hidden');
    updateFlopEvalProgress();

    dealFlopEvalHand();
}

async function dealFlopEvalHand() {
    // Pick random (situation, stackDepth) combo
    const situations = [...flopEval.situations];
    const depths = [...flopEval.depths];
    const sitKey = situations[Math.floor(Math.random() * situations.length)];
    const depthVal = depths[Math.floor(Math.random() * depths.length)];

    const sit = FLOP_EVAL_SITUATIONS.find(s => s.key === sitKey);
    const sd  = STACK_DEPTHS.find(s => s.value === depthVal);

    // Override flopState for this hand
    flopState.hero       = sit.hero;
    flopState.villain    = sit.villain;
    flopState.stackDepth = sd;
    flopState.scenario   = sit.scenario || null;

    // Store current combo for result tracking
    flopEval._currentCombo = { key: sitKey, hero: sit.hero, villain: sit.villain, stackDepth: depthVal, label: sit.label, sdLabel: sd.label };

    // Update display
    document.getElementById('hero-pos-label').textContent    = sit.hero;
    document.getElementById('villain-pos-label').textContent = sit.villain;
    document.getElementById('flop-config-display').textContent = `${sit.hero} vs ${sit.villain} — ${sd.label}`;

    // Prominent context strip
    const ctx = document.getElementById('flop-eval-context');
    if (ctx) {
        ctx.classList.remove('hidden');
        document.getElementById('flop-ctx-sit').textContent   = sit.label;
        document.getElementById('flop-ctx-stack').textContent = sd.label;
    }

    await dealFlopHand();
}

function updateFlopEvalProgress() {
    const pct = Math.round((flopEval.handsDone / flopEval.handCount) * 100);
    document.getElementById('flop-eval-progress-bar').style.width = `${pct}%`;
    document.getElementById('flop-eval-progress-label').textContent = `${flopEval.handsDone} / ${flopEval.handCount}`;
}

function trackFlopEvalResult(isCorrect, userAction, correctAction) {
    if (!flopEval.active || !flopEval._currentCombo) return;
    const { key, hero, villain, stackDepth, label, sdLabel } = flopEval._currentCombo;
    const rKey = `${key}@${stackDepth}`;
    if (!flopEval.results[rKey]) {
        flopEval.results[rKey] = { correct: 0, total: 0, hero, villain, stackDepth, label, sdLabel, errors: {} };
    }
    flopEval.results[rKey].total++;
    if (isCorrect) {
        flopEval.results[rKey].correct++;
    } else if (userAction && correctAction && userAction !== correctAction) {
        const errKey = `${userAction}→${correctAction}`;
        flopEval.results[rKey].errors[errKey] = (flopEval.results[rKey].errors[errKey] || 0) + 1;
    }

    flopEval.handsDone++;
    updateFlopEvalProgress();

    const nextBtn = document.getElementById('flop-next-btn');
    if (flopEval.handsDone >= flopEval.handCount) {
        nextBtn.textContent = 'Voir les résultats →';
        nextBtn.onclick = showFlopEvalResults;
    } else {
        nextBtn.textContent = 'Main suivante →';
        nextBtn.onclick = dealFlopEvalHand;
    }
}

function showFlopEvalResults() {
    document.getElementById('flop-practice-screen').classList.remove('active');
    document.getElementById('flop-results-screen').classList.add('active');
    renderFlopResults();
}

const ACTION_LABELS_FR = {
    fold:  'Fold',
    call:  'Call',
    raise: 'Check-Raise',
    bet:   'Bet',
    check: 'Check',
};

function renderFlopResults() {
    const overall   = document.getElementById('flop-results-overall');
    const tableWrap = document.getElementById('flop-results-table');

    const allResults   = Object.values(flopEval.results);
    const totalCorrect = allResults.reduce((s, r) => s + r.correct, 0);
    const totalTotal   = allResults.reduce((s, r) => s + r.total, 0);
    const globalPct    = totalTotal > 0 ? Math.round((totalCorrect / totalTotal) * 100) : 0;
    const globalColor  = globalPct >= 75 ? '#28a745' : globalPct >= 50 ? '#f0ad4e' : '#dc3545';

    // Aggregate all errors
    const allErrors = {};
    allResults.forEach(r => {
        Object.entries(r.errors || {}).forEach(([k, v]) => {
            allErrors[k] = (allErrors[k] || 0) + v;
        });
    });

    // Tendency analysis
    const tooPassive    = (allErrors['fold→call']  || 0) + (allErrors['fold→raise']  || 0) + (allErrors['check→bet'] || 0);
    const tooAggressive = (allErrors['call→fold']  || 0) + (allErrors['raise→fold']  || 0) + (allErrors['bet→check'] || 0);
    const wrongIntensity = (allErrors['call→raise'] || 0) + (allErrors['raise→call'] || 0);
    const totalErrors   = Object.values(allErrors).reduce((s, v) => s + v, 0);

    let tendanceHtml = '';
    if (totalErrors > 0) {
        const dom = Math.max(tooPassive, tooAggressive, wrongIntensity);
        if (dom === tooPassive && tooPassive > 0) {
            tendanceHtml = `<div class="results-tendency tendency-passive">
                📉 Trop passif — tu fold / check trop souvent (${tooPassive} erreur${tooPassive > 1 ? 's' : ''})
            </div>`;
        } else if (dom === tooAggressive && tooAggressive > 0) {
            tendanceHtml = `<div class="results-tendency tendency-aggressive">
                📈 Trop agressif — tu raise / bet trop souvent (${tooAggressive} erreur${tooAggressive > 1 ? 's' : ''})
            </div>`;
        } else if (wrongIntensity > 0) {
            tendanceHtml = `<div class="results-tendency tendency-neutral">
                🔄 Bonne direction mais intensité incorrecte — call/raise confondus (${wrongIntensity} erreur${wrongIntensity > 1 ? 's' : ''})
            </div>`;
        }

        // Top global errors
        const topErrors = Object.entries(allErrors)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 4);
        if (topErrors.length > 0) {
            tendanceHtml += `<div class="results-top-errors">
                ${topErrors.map(([k, n]) => {
                    const [ua, ca] = k.split('→');
                    return `<span class="error-chip-global">
                        ${ACTION_LABELS_FR[ua] || ua} → ${ACTION_LABELS_FR[ca] || ca}: ${n}×
                    </span>`;
                }).join('')}
            </div>`;
        }
    } else if (totalTotal > 0) {
        tendanceHtml = `<div class="results-tendency tendency-good">✨ Excellent — aucune erreur d'action !</div>`;
    }

    overall.innerHTML = `
        <div class="results-score" style="color:${globalColor}">
            ${totalCorrect} / ${totalTotal}
            <span class="results-pct">${globalPct}%</span>
        </div>
        ${tendanceHtml}
    `;

    // Per-situation breakdown (sorted worst first)
    const rows = allResults.sort((a, b) => (a.correct / a.total) - (b.correct / b.total));

    let html = '';
    rows.forEach(r => {
        const pct   = Math.round((r.correct / r.total) * 100);
        const bg    = pct >= 75 ? '#d4edda' : pct >= 50 ? '#fff3cd' : '#f8d7da';
        const color = pct >= 75 ? '#155724' : pct >= 50 ? '#856404' : '#721c24';

        const errEntries = Object.entries(r.errors || {}).sort((a, b) => b[1] - a[1]);
        const errHtml = errEntries.length > 0
            ? errEntries.map(([k, n]) => {
                const [ua, ca] = k.split('→');
                return `<span class="error-chip">✗ ${ACTION_LABELS_FR[ua] || ua} → ${ACTION_LABELS_FR[ca] || ca}: ${n}×</span>`;
            }).join('')
            : '';

        html += `
            <div class="result-card-item">
                <div class="result-card-top">
                    <div class="result-card-identity">
                        <span class="result-sit-badge">${r.label}</span>
                        <span class="result-stack-pill">${r.sdLabel}</span>
                    </div>
                    <div class="result-score-badge" style="background:${bg};color:${color}">
                        <span class="result-score-pct">${pct}%</span>
                        <span class="result-score-frac">${r.correct}/${r.total}</span>
                    </div>
                </div>
                ${errHtml ? `<div class="result-sit-errors">${errHtml}</div>` : ''}
            </div>
        `;
    });

    tableWrap.innerHTML = html || '<p style="color:#888;text-align:center">Aucun résultat</p>';
}

function flopResultsBackToMenu() {
    document.getElementById('flop-results-screen').classList.remove('active');
    document.getElementById('flop-config-screen').classList.add('active');
    document.getElementById('flop-eval-progress').classList.add('hidden');
    document.getElementById('flop-eval-context').classList.add('hidden');
    const nextBtn = document.getElementById('flop-next-btn');
    nextBtn.textContent = 'Next Hand →';
    nextBtn.onclick = dealFlopHand;
}

function flopResultsRetry() {
    document.getElementById('flop-results-screen').classList.remove('active');
    flopEval.handsDone = 0;
    flopEval.results = {};
    flopPractice.stats = { correct: 0, total: 0 };
    updateFlopStats();

    const practiceScr = document.getElementById('flop-practice-screen');
    practiceScr.classList.add('active');
    const progress = document.getElementById('flop-eval-progress');
    progress.classList.remove('hidden');
    updateFlopEvalProgress();

    dealFlopEvalHand();
}

// ─── Practice Session ─────────────────────────

function startFlopPractice(configScr, practiceScr) {
    const { hero, villain, stackDepth } = flopState;

    const scenarioSuffix = flopState.scenario === 'limp' ? ' (Limp)' : flopState.scenario === 'raise' ? ' (Raise)' : '';
    document.getElementById('flop-config-display').textContent =
        `${hero} vs ${villain}${scenarioSuffix} — ${stackDepth.label}`;
    document.getElementById('hero-pos-label').textContent = hero;
    document.getElementById('villain-pos-label').textContent = villain;

    flopPractice.stats = { correct: 0, total: 0 };
    updateFlopStats();

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
    const isBBDefense = hero === 'BB';

    const feedback = document.getElementById('flop-feedback');
    const nextBtn  = document.getElementById('flop-next-btn');
    if (feedback) feedback.className = 'feedback hidden';
    if (nextBtn)  nextBtn.style.display = 'none';
    document.getElementById('flop-pot-label').textContent = '';

    try {
        if (isBBDefense) {
            const res = await fetch('/api/flop/bb-deal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ villain_position: villain, stack_depth: stackDepth.value }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Erreur serveur');

            flopPractice.heroHand        = data.bb_cards;
            flopPractice.villainHand     = data.villain_cards;
            flopPractice.communityCards  = data.flop_cards;

            renderHeroCards();
            renderCommunityCards();
            renderVillainCardsFaceDown();
            showBBVillainBet(data.villain_sizing, stackDepth.value);

        } else {
            const res = await fetch('/api/flop/hero-hand', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ hero, villain, stackDepth: stackDepth.value, scenario: flopState.scenario }),
            });
            const data = await res.json();

            let deck = buildDeck();
            flopPractice.heroHand = extractCardsForHand(data.hand, deck);
            flopPractice.villainHand = [];
            deck = shuffle(deck);
            deck.shift(); deck.shift(); // skip villain slots
            deck.shift();               // burn
            flopPractice.communityCards = [deck.shift(), deck.shift(), deck.shift()];

            renderHeroCards();
            renderCommunityCards();
            renderVillainCardsFaceDown();
            buildActionButtons();
            document.getElementById('flop-situation').textContent = 'Bet ou Check ?';
        }

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
        scenario: flopState.scenario,
    };

    const supported = { BTN: ['BB', 'SB'], CO: ['BB'], SB: ['BB'] };
    if (!supported[hero] || !supported[hero].includes(villain)) {
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
        // BTN/CO vs BB
        TRES_DRY:     '#27ae60',
        INTERMEDIAIRE:'#e67e22',
        DRAWY:        '#c0392b',
        // BTN vs SB — vert = range bet, orange = bon, rouge = difficile
        range_low_mid_pair: '#27ae60',
        range_nine_eight:   '#27ae60',
        range_low_board:    '#27ae60',
        qjt_high:           '#e67e22',
        double_broadway:    '#e67e22',
        ak_dry:             '#e67e22',
        high_pair:          '#c0392b',
        ak_drawy:           '#c0392b',
        monocolor:          '#8e44ad',
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

    if (isCorrect) flopPractice.stats.correct++;
    flopPractice.stats.total++;
    updateFlopStats();

    if (flopEval.active) {
        trackFlopEvalResult(isCorrect, userAction, data.correct_action);
    } else if (nextBtn) {
        nextBtn.textContent = 'Next Hand →';
        nextBtn.onclick = dealFlopHand;
    }
    if (nextBtn) nextBtn.style.display = 'block';
}

function resetActionArea() {
    const feedback = document.getElementById('flop-feedback');
    const nextBtn = document.getElementById('flop-next-btn');
    if (feedback) feedback.className = 'feedback hidden';
    if (nextBtn) nextBtn.style.display = 'none';

    if (flopState.hero === 'BB') {
        buildBBDefenseButtons();
        document.getElementById('flop-situation').textContent = 'Fold, Call ou Check-Raise ?';
    } else {
        buildActionButtons();
        document.getElementById('flop-situation').textContent = 'Bet ou Check ?';
    }
}

// ─── Villain Card Rendering ───────────────────

function renderVillainCardsFaceDown() {
    const container = document.getElementById('villain-cards');
    if (!container) return;
    container.innerHTML = `
        <div class="card card-back"></div>
        <div class="card card-back"></div>
    `;
}

function revealVillainCards() {
    const cards = flopPractice.villainHand;
    if (!cards || cards.length < 2) return;
    const container = document.getElementById('villain-cards');
    const cardEls = container.querySelectorAll('.card');
    cards.forEach((card, idx) => {
        const el = cardEls[idx];
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

// ─── BB Defense Mode ─────────────────────────

function showBBVillainBet(villainSizing, stackDepthValue) {
    document.getElementById('flop-pot-label').textContent =
        `Pot: ${stackDepthValue * 2}bb — Villain cbet ${villainSizing}% du pot`;
    document.getElementById('flop-situation').textContent = 'Fold, Call ou Check-Raise ?';
    buildBBDefenseButtons();
}

function buildBBDefenseButtons() {
    const group = document.getElementById('flop-btn-group');
    if (!group) return;
    group.innerHTML = '';
    flopTurn.pendingAction = null;

    group.appendChild(makeActionBtn('Fold',         '#c0392b', () => selectBBDefenseAction('fold')));
    group.appendChild(makeActionBtn('Call',         '#27ae60', () => selectBBDefenseAction('call')));
    group.appendChild(makeActionBtn('Check-Raise',  '#8e44ad', () => selectBBDefenseAction('raise')));
}

function selectBBDefenseAction(action) {
    flopTurn.pendingAction = action;
    document.querySelectorAll('#flop-btn-group > .flop-action-btn').forEach(btn => {
        btn.style.opacity = '0.4';
    });

    if (action === 'raise') {
        showBBRaiseSizingButtons();
    } else {
        submitBBDefense(action, null);
    }
}

const BB_RAISE_SIZINGS = [2.5, 2.75, 3, 3.5, 4, 5];

function showBBRaiseSizingButtons() {
    const group = document.getElementById('flop-btn-group');
    const old = group.querySelector('.sizing-row');
    if (old) old.remove();

    const row = document.createElement('div');
    row.className = 'sizing-row';
    row.style.cssText = 'display:flex;gap:8px;justify-content:center;margin-top:8px;flex-wrap:wrap;';

    BB_RAISE_SIZINGS.forEach(mult => {
        const btn = document.createElement('button');
        btn.className = 'flop-action-btn sizing-btn';
        btn.textContent = `${mult}x`;
        btn.style.cssText = 'background:#8e44ad;min-width:70px;padding:8px 14px;font-size:0.9rem;';
        btn.addEventListener('click', () => submitBBDefense('raise', mult));
        row.appendChild(btn);
    });

    group.appendChild(row);
    document.getElementById('flop-situation').textContent = 'Choisissez le sizing du check-raise :';
}

async function submitBBDefense(action, sizing) {
    document.querySelectorAll('.flop-action-btn').forEach(btn => btn.disabled = true);

    const { villain, stackDepth } = flopState;
    const payload = {
        hero_cards:       flopPractice.heroHand.map(c => ({ rank: c.rank, suit: c.suit })),
        board_cards:      flopPractice.communityCards.map(c => ({ rank: c.rank, suit: c.suit })),
        villain_position: villain,
        stack_depth:      stackDepth.value,
        user_action:      action,
        user_sizing:      sizing,
    };

    try {
        const res = await fetch('/api/flop/bb-defense', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Erreur serveur');

        revealVillainCards();
        showBBDefenseFeedback(data, action, sizing);

    } catch (err) {
        console.error('bb-defense error:', err);
        document.getElementById('flop-feedback').className = 'feedback incorrect';
        document.getElementById('flop-feedback').innerHTML =
            `<div class="feedback-title">Erreur : ${err.message}</div>`;
        document.getElementById('flop-next-btn').style.display = 'block';
    }
}

function showBBDefenseFeedback(data, userAction, userSizing) {
    const feedback = document.getElementById('flop-feedback');
    const nextBtn  = document.getElementById('flop-next-btn');

    const isCorrect = data.correct;
    feedback.className = `feedback ${isCorrect ? 'correct' : 'incorrect'}`;

    const textureColors = {
        TRES_DRY:      '#27ae60',
        INTERMEDIAIRE: '#e67e22',
        DRAWY:         '#c0392b',
    };
    const tc = textureColors[data.texture] || '#888';
    const textureBadge = `<span style="background:${tc};color:#fff;padding:2px 8px;border-radius:12px;font-size:0.8rem;font-weight:700;">${data.texture_label}</span>`;

    const actionLabels = { fold: 'Fold', call: 'Call', raise: 'Check-Raise' };
    const correctLabel = data.correct_sizing
        ? `${actionLabels[data.correct_action]} ${data.correct_sizing}x`
        : actionLabels[data.correct_action];
    const userLabel = userSizing
        ? `${actionLabels[userAction] || userAction} ${userSizing}x`
        : (actionLabels[userAction] || userAction);

    feedback.innerHTML = `
        <div class="feedback-title">${isCorrect ? '✓ Correct !' : '✗ Incorrect'}</div>
        <div class="feedback-detail" style="margin-top:6px;">
            Board : ${textureBadge} — Villain cbet ${data.villain_sizing}% du pot
        </div>
        <div class="feedback-detail" style="margin-top:4px;">
            Ta main : <em>${data.hand_label}</em>
        </div>
        <div class="feedback-detail" style="margin-top:4px;">
            ${isCorrect ? '' : `Bonne réponse : <strong>${correctLabel}</strong><br>`}Tu as joué : <strong>${userLabel}</strong>
        </div>
    `;

    if (isCorrect) flopPractice.stats.correct++;
    flopPractice.stats.total++;
    updateFlopStats();

    if (flopEval.active) {
        trackFlopEvalResult(isCorrect, userAction, data.correct_action);
    } else if (nextBtn) {
        nextBtn.textContent = 'Next Hand →';
        nextBtn.onclick = dealFlopHand;
    }
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

// ─── Guide Mode ───────────────────────────────

const FLOP_GUIDE_DATA = {};

// BTN / CO vs BB  (c-bet avec position)
FLOP_GUIDE_DATA['BTN/BB'] = {
    type: 'cbet',
    note: 'Vous avez la position. BB check le flop à vous.',
    cats: [
        {
            label: 'Très Dry', color: 'green',
            examples: 'K72r · A62r · K82r',
            criteria: 'Carte haute + cartes basses espacées, pas de FD',
            freq: 'Range entier', size: 25, sizeDeep: 33,
            bet: ['Toutes les mains'], check: [],
        },
        {
            label: 'Intermédiaire', color: 'yellow',
            examples: 'K87s · Q74r · T96r',
            criteria: 'Board haut avec flush draw, ou connectivité moyenne',
            freq: '3/4 des mains', size: 33, sizeDeep: 50,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort', 'Backdoor'],
            check: ['Weak', 'Draw Moyen', 'Air'],
        },
        {
            label: 'Drawy', color: 'red',
            examples: '876s · T98s · 765r · monocolor bas',
            criteria: 'Board bas (≤7 high), connecté ou monotone',
            freq: '1/2 des mains', size: 50, sizeDeep: 66,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort', 'Backdoor'],
            check: ['Weak', 'Draw Moyen', 'Air'],
        },
    ],
};
FLOP_GUIDE_DATA['CO/BB'] = FLOP_GUIDE_DATA['BTN/BB'];

// BTN vs SB  (c-bet avec position)
FLOP_GUIDE_DATA['BTN/SB'] = {
    type: 'cbet',
    note: 'Vous avez la position sur le SB défendeur.',
    cats: [
        {
            label: 'Pairé low/mid (2-9)', color: 'green',
            examples: '882r · 773s · 996r',
            criteria: 'Flop pairé, carte de la paire entre 2 et 9',
            freq: 'Range entier', size: 33,
            bet: ['Toutes les mains'], check: [],
        },
        {
            label: '9 / 8 high', color: 'green',
            examples: '983r · 872s · 975r',
            criteria: 'Carte la plus haute = 9 ou 8, board non pairé',
            freq: 'Range entier', size: 50,
            bet: ['Toutes les mains'], check: [],
        },
        {
            label: 'Low board (≤7 high)', color: 'green',
            examples: '742r · 653s · 752r',
            criteria: 'Carte la plus haute ≤ 7',
            freq: 'Range entier', size: 50,
            bet: ['Toutes les mains'], check: [],
        },
        {
            label: 'Q/J/T high (1 broadway)', color: 'yellow',
            examples: 'Q84r · J73s · T62r',
            criteria: '1 seule carte broadway, board non pairé',
            freq: '2/3 des mains', size: 50,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort', 'Backdoor'],
            check: ['Weak', 'Draw Moyen', 'Air'],
        },
        {
            label: 'Double Broadway', color: 'yellow',
            examples: 'KQ7r · QJTs · AJ4r',
            criteria: '2+ cartes broadway (≥T), hors A/K high sec',
            freq: '2/3 des mains', size: 50,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort', 'Backdoor'],
            check: ['Weak', 'Draw Moyen', 'Air'],
        },
        {
            label: 'A/K high sec', color: 'yellow',
            examples: 'A72r · K83r · A92r',
            criteria: 'A ou K top card + cartes basses espacées (gap ≥5)',
            freq: '2/3 des mains', size: 33,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort', 'Backdoor'],
            check: ['Weak', 'Draw Moyen', 'Air'],
        },
        {
            label: 'A/K high drawy', color: 'orange',
            examples: 'A87s · K97r · A76r',
            criteria: 'A ou K avec cartes connectées ou flush draw',
            freq: '1/2 des mains', size: 50,
            bet: ['Monster', 'Strong', 'Draw Fort'],
            check: ['Medium', 'Weak', 'Backdoor', 'Draw Moyen', 'Air'],
        },
        {
            label: 'Pairé haut (T+)', color: 'orange',
            examples: 'TT7r · QQ3s · JJ5r',
            criteria: 'Flop pairé, carte de la paire ≥ T',
            freq: '30% des mains', size: 33,
            bet: ['Monster'],
            check: ['Strong', 'Medium', 'Weak', 'Draw Fort', 'Air'],
        },
        {
            label: 'Monocolor', color: 'red',
            examples: 'Q87♥ · K53♠ · 976♣',
            criteria: 'Les 3 cartes de la même couleur',
            freq: '<50% des mains', size: 33,
            bet: ['Monster', 'Strong'],
            check: ['Medium', 'Weak', 'Draw Moyen', 'Backdoor', 'Air'],
        },
    ],
};

// BB defense vs BTN / CO  (sans position)
FLOP_GUIDE_DATA['BB/BTN'] = {
    type: 'defense',
    note: 'Villain a c-bet le flop. Vous défendez sans position.',
    cats: [
        {
            label: 'Très Dry', color: 'green',
            examples: 'K72r · A62r · K82r',
            villainSize: 25,
            raise: ['Monster', 'Overpaire > board', 'TP + bonne kicker (A/K)', 'Flush Draw', 'OESD', 'Gutshot', 'Paire basse (bluff)', 'Q/J high + BDFD + BDSFD'],
            call:  ['Strong (TP)', 'Medium (MP)', 'Weak (BP)', 'A/K high + BDFD'],
            fold:  ['Air pur sans backdoor'],
        },
        {
            label: 'Intermédiaire', color: 'yellow',
            examples: 'K87s · Q74r · T96r',
            villainSize: 33,
            raise: ['Monster', 'TP + AK suited (TPBK)', 'OESD', 'Flush Draw', 'Gutshot + BDFD', 'A-high + BDSFD + BDFD'],
            call:  ['A-high non pairé', '2 overcards + BDFD', 'Strong', 'Medium', 'Weak'],
            fold:  ['Air sans draw', 'Draw Moyen pur'],
        },
        {
            label: 'Drawy', color: 'red',
            examples: '876s · T98s · 765r',
            villainSize: 50,
            raise: ['Set / Trips', 'Quinte', 'OESD', 'Flush Draw'],
            call:  ['Overpaire', 'Top Pair', 'Flush', 'A-high + BDFD', '2 overcards + BDFD', 'Mid Pair'],
            fold:  ['Paire basse sans draws', 'Weak pur', 'Backdoor seul'],
        },
    ],
};
FLOP_GUIDE_DATA['BB/CO'] = FLOP_GUIDE_DATA['BB/BTN'];

// SB vs BB raise — BvB hors position
FLOP_GUIDE_DATA['SB/BB'] = {
    type: 'cbet',
    note: 'BvB — vous avez raise en SB, BB a suivi. Vous êtes HOP.',
    cats: [
        {
            label: 'Avantage nuts (A/K high sec)', color: 'lime',
            examples: 'A72r · K83r · A92r',
            criteria: 'A ou K top card, cartes basses espacées',
            freq: '3/4 des mains', size: 50,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort'],
            check: ['Weak', 'Backdoor', 'Air'],
        },
        {
            label: 'Single BW sec / Double BW', color: 'lime',
            examples: 'Q84r · KQ7r · QJTs',
            criteria: '1 broadway sec (Q/J/T) ou 2+ broadway',
            freq: '70% des mains', size: 33,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort'],
            check: ['Weak', 'Backdoor', 'Air'],
        },
        {
            label: 'Single BW connecté / Low sec', color: 'yellow',
            examples: 'Q87r · J98s · 942r',
            criteria: 'Single broadway connecté, ou board bas déconnecté',
            freq: '1/2 des mains', size: 50,
            bet: ['Monster', 'Strong', 'Draw Fort'],
            check: ['Medium', 'Weak', 'Backdoor', 'Air'],
        },
        {
            label: 'Pairé', color: 'orange',
            examples: 'T72r · K85p · 882s',
            criteria: 'Flop pairé, toute hauteur',
            freq: '3/4 std', freqDeep: '1/2 des mains',
            size: 25,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort'],
            betDeep: ['Monster', 'Strong'],
            check: ['Weak', 'Backdoor', 'Air'],
            checkDeep: ['Medium', 'Weak', 'Draw Fort', 'Backdoor', 'Air'],
        },
        {
            label: 'Monocolor', color: 'red',
            examples: 'Q87♥ · 976♠ · K43♣',
            criteria: 'Les 3 cartes de la même couleur',
            freq: '1/3 std', freqDeep: '1/2 des mains',
            size: 25,
            bet: ['Monster'],
            betDeep: ['Monster', 'Strong'],
            check: ['Strong', 'Medium', 'Weak', 'Draw Fort', 'Backdoor', 'Air'],
            checkDeep: ['Medium', 'Weak', 'Draw Fort', 'Backdoor', 'Air'],
        },
        {
            label: 'Bas connecté', color: 'red',
            examples: '876r · 975s · 753r',
            criteria: 'Toutes les cartes ≤9, gap total ≤4',
            freq: '30% std', freqDeep: 'Check range entier',
            size: 66, sizeDeep: null,
            bet: ['Monster'],
            betDeep: [],
            check: ['Strong', 'Medium', 'Weak', 'Draw Fort', 'Backdoor', 'Air'],
            checkDeep: ['Toutes les mains'],
        },
    ],
};

// SB vs BB limp — BvB hors position
FLOP_GUIDE_DATA['SB/BB_limp'] = {
    type: 'cbet',
    note: 'BvB — vous avez limp en SB, BB a check. Vous êtes HOP.',
    cats: [
        {
            label: 'Pairé low (2-6)', color: 'red',
            examples: '662r · 332s · 554r',
            criteria: 'Flop pairé, carte de la paire entre 2 et 6',
            freq: 'Check range entier', size: null,
            bet: [], check: ['Toutes les mains'],
        },
        {
            label: 'Pairé mid (7-9)', color: 'orange',
            examples: '772r · 885s · 993r',
            criteria: 'Flop pairé, carte de la paire entre 7 et 9',
            freq: '1/3 des mains', freqShallow: 'Check (20bb)',
            size: 50, sizeShallow: null,
            bet: ['Monster', 'Strong'],
            betShallow: [],
            check: ['Medium', 'Weak', 'Draw Fort', 'Backdoor', 'Air'],
            checkShallow: ['Toutes les mains'],
        },
        {
            label: 'Pairé haut (T+)', color: 'yellow',
            examples: 'TT7r · QQ3s · JJ5r',
            criteria: 'Flop pairé, carte de la paire ≥ T',
            freq: '~40% std · ≥50% deep', size: 50,
            bet: ['Monster', 'Strong', 'Medium'],
            check: ['Weak', 'Draw Fort', 'Backdoor', 'Air'],
        },
        {
            label: 'A-high / Double Broadway', color: 'yellow',
            examples: 'A87s · AJ4r · KQ7r',
            criteria: 'As en top card, ou 2+ broadway',
            freq: '~40% std · 1/2 deep', size: 50,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort'],
            check: ['Weak', 'Backdoor', 'Air'],
        },
        {
            label: 'Connecté ou monocolor', color: 'red',
            examples: '876s · 975r · Q87♥',
            criteria: 'Board connecté (gap ≤4) ou monotone, sans broadway',
            freq: '~25% des mains', size: 50,
            bet: ['Monster'],
            check: ['Strong', 'Medium', 'Weak', 'Draw Fort', 'Backdoor', 'Air'],
        },
        {
            label: 'Déconnecté', color: 'lime',
            examples: 'K72r · Q83s · J62r',
            criteria: 'Board déconnecté non A-high et non 2+ broadway',
            freq: '1/2 des mains', size: 50,
            bet: ['Monster', 'Strong', 'Medium', 'Draw Fort', 'Showdown'],
            check: ['Weak', 'Backdoor', 'Air'],
        },
    ],
};

function showFlopGuide(configScr) {
    const { hero, villain, stackDepth, scenario } = flopState;
    const depth = stackDepth.value;

    let key;
    if (hero === 'SB' && villain === 'BB') {
        key = scenario === 'limp' ? 'SB/BB_limp' : 'SB/BB';
    } else {
        key = `${hero}/${villain}`;
    }

    const data = FLOP_GUIDE_DATA[key];
    if (!data) return;

    const typeLabel = data.type === 'defense' ? 'Défense' : 'C-Bet';
    const sitLabel = (hero === 'SB' && villain === 'BB' && scenario)
        ? `SB vs BB (${scenario === 'limp' ? 'SB Limp' : 'SB Raise'})`
        : `${hero} vs ${villain}`;
    document.getElementById('guide-title').textContent = `${typeLabel} · ${sitLabel} — ${stackDepth.label}`;
    document.getElementById('guide-content').innerHTML = renderGuideContent(data, depth);

    configScr.classList.remove('active');
    document.getElementById('flop-guide-screen').classList.add('active');
}

function renderGuideContent(data, depth) {
    const isDeep    = depth >= 70;
    const isShallow = depth <= 30;

    let html = `<p class="guide-note">${data.note}</p><div class="guide-cats">`;

    for (const cat of data.cats) {
        const freq = (isDeep && cat.freqDeep)    ? cat.freqDeep
                   : (isShallow && cat.freqShallow) ? cat.freqShallow
                   : cat.freq;

        const size = (isDeep    && cat.sizeDeep    !== undefined) ? cat.sizeDeep
                   : (isShallow && cat.sizeShallow  !== undefined) ? cat.sizeShallow
                   : cat.size;

        html += `<div class="guide-cat guide-cat--${cat.color}">`;
        html += `<div class="guide-cat-header">`;
        html += `<span class="guide-cat-label">${cat.label}</span>`;
        html += `<div class="guide-cat-stats">`;
        html += `<span class="guide-freq-badge">${freq}</span>`;
        if (size) html += `<span class="guide-size-badge">${size}% pot</span>`;
        if (data.type === 'defense') html += `<span class="guide-villain-size">Villain: ${cat.villainSize}%</span>`;
        html += `</div></div>`;

        html += `<p class="guide-cat-examples">${cat.examples}</p>`;
        if (cat.criteria) html += `<p class="guide-cat-criteria">${cat.criteria}</p>`;

        if (data.type === 'cbet') {
            const bet   = (isDeep && cat.betDeep)     ? cat.betDeep
                        : (isShallow && cat.betShallow) ? cat.betShallow
                        : cat.bet;
            const check = (isDeep && cat.checkDeep)     ? cat.checkDeep
                        : (isShallow && cat.checkShallow) ? cat.checkShallow
                        : cat.check;

            if (bet.length) {
                html += `<div class="guide-hands">`;
                html += `<span class="guide-hands-label guide-hands-label--bet">✓ Bet</span>`;
                html += bet.map(h => `<span class="guide-hand-tag guide-hand-tag--bet">${h}</span>`).join('');
                html += `</div>`;
            }
            if (check.length) {
                html += `<div class="guide-hands">`;
                html += `<span class="guide-hands-label guide-hands-label--check">✗ Check</span>`;
                html += check.map(h => `<span class="guide-hand-tag guide-hand-tag--check">${h}</span>`).join('');
                html += `</div>`;
            }
        } else {
            const sections = [
                { key: 'raise', icon: '↑', cls: 'raise', label: 'Raise' },
                { key: 'call',  icon: '→', cls: 'call',  label: 'Call'  },
                { key: 'fold',  icon: '✗', cls: 'fold',  label: 'Fold'  },
            ];
            for (const { key, icon, cls, label } of sections) {
                if (cat[key] && cat[key].length) {
                    html += `<div class="guide-hands">`;
                    html += `<span class="guide-hands-label guide-hands-label--${cls}">${icon} ${label}</span>`;
                    html += cat[key].map(h => `<span class="guide-hand-tag guide-hand-tag--${cls}">${h}</span>`).join('');
                    html += `</div>`;
                }
            }
        }

        html += `</div>`;
    }

    html += `</div>`;
    return html;
}