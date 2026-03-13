function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

document.addEventListener('DOMContentLoaded', () => {
    const config = document.getElementById('finance-config');
    if (!config) return;

    const transactionModalEl = document.getElementById('transactionModal');
    const transactionModal = new bootstrap.Modal(transactionModalEl);
    const transactionForm = document.getElementById('transactionForm');
    const modalTitle = document.getElementById('modalTitle');
    const submitBtn = document.getElementById('submitBtn');
    const chatWindow = document.getElementById('chat-window');
    const chartLabelsEl = document.getElementById('chart-labels');
    const chartDataEl = document.getElementById('chart-data');
    const chartHintEl = document.getElementById('expenseChartHint');
    const chartCanvasEl = document.getElementById('expenseChart');
    const fabPupils = document.querySelectorAll('.octo-pupil');
    const octoFab = document.querySelector('.octo-fab');
    const octoCreature = document.querySelector('.octo-fab-creature');
    const appMainContent = document.querySelector('.app-main-content');
    let chatOpen = false;

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function resetDateTime() {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        document.getElementById('datetime_now').value = now.toISOString().slice(0, 16);
    }

    function openAddModal() {
        transactionForm.reset();
        transactionForm.action = config.dataset.addUrl;
        modalTitle.innerText = 'New Transaction';
        submitBtn.innerText = 'Save Transaction';
        resetDateTime();
        transactionModal.show();
    }

    function openEditModal(tid) {
        modalTitle.innerText = 'Edit Transaction';
        submitBtn.innerText = 'Update Transaction';
        const editUrl = config.dataset.editTemplate.replace('0', tid);
        transactionForm.action = editUrl;

        fetch(editUrl)
            .then((response) => response.json())
            .then((data) => {
                transactionForm.querySelector('[name="amount"]').value = data.amount;
                transactionForm.querySelector('[name="currency"]').value = data.currency;
                transactionForm.querySelector('[name="type"]').value = data.type;
                transactionForm.querySelector('[name="category"]').value = data.category;
                transactionForm.querySelector('[name="date"]').value = data.date;
                transactionForm.querySelector('[name="note"]').value = data.note;
                transactionModal.show();
            })
            .catch(() => alert('Error fetching data.'));
    }

    function applyChatState(nextOpen) {
        chatOpen = nextOpen;
        chatWindow.classList.toggle('chat-window-open', chatOpen);
        chatWindow.classList.toggle('chat-window-closed', !chatOpen);
        chatWindow.setAttribute('aria-hidden', chatOpen ? 'false' : 'true');

        if (octoFab) {
            octoFab.classList.toggle('chat-fab-open', chatOpen);
            octoFab.setAttribute('aria-expanded', chatOpen ? 'true' : 'false');
        }

        if (chatOpen) {
            window.setTimeout(() => {
                const input = document.getElementById('chat-input');
                if (input) input.focus();
            }, 220);
        }
    }

    function toggleChat() {
        applyChatState(!chatOpen);
    }

    function moveFabPupil(pupil, centerX, centerY, clientX, clientY) {
        const dx = clientX - centerX;
        const dy = clientY - centerY;
        const angle = Math.atan2(dy, dx);
        const distance = Math.min(5.5, Math.hypot(dx, dy) / 22);
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance;
        pupil.style.transform = `translate(${x.toFixed(2)}px, ${y.toFixed(2)}px)`;
    }

    function bindFabEyeTracking() {
        if (!fabPupils.length) return;
        const onMove = (evt) => {
            fabPupils.forEach((pupil) => {
                const box = pupil.getBoundingClientRect();
                moveFabPupil(
                    pupil,
                    box.left + box.width / 2,
                    box.top + box.height / 2,
                    evt.clientX,
                    evt.clientY
                );
            });
        };
        window.addEventListener('mousemove', onMove, { passive: true });
        window.addEventListener('touchmove', (evt) => {
            const touch = evt.touches && evt.touches[0];
            if (!touch) return;
            onMove({ clientX: touch.clientX, clientY: touch.clientY });
        }, { passive: true });
    }

    function bindFabPhysics() {
        if (!octoFab) return;

        const state = { x: 0, y: 0, vx: 0, vy: 0 };
        const pointer = {
            x: window.innerWidth / 2,
            y: window.innerHeight / 2,
            activeUntil: 0,
        };
        const radius = 72;

        const onPoint = (x, y) => {
            pointer.x = x;
            pointer.y = y;
            pointer.activeUntil = performance.now() + 2200;
        };

        window.addEventListener('mousemove', (evt) => onPoint(evt.clientX, evt.clientY), { passive: true });
        window.addEventListener('touchmove', (evt) => {
            const touch = evt.touches && evt.touches[0];
            if (!touch) return;
            onPoint(touch.clientX, touch.clientY);
        }, { passive: true });

        let lastTime = performance.now();
        const tick = (now) => {
            const dt = Math.min((now - lastTime) / 16.666, 2.0);
            lastTime = now;

            const idleX = Math.sin(now * 0.0012) * 24.6;
            const idleY = Math.cos(now * 0.0015) * 22.2;
            let targetX = idleX;
            let targetY = idleY;

            const rect = octoFab.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            const dx = pointer.x - cx;
            const dy = pointer.y - cy;
            const dist = Math.hypot(dx, dy);
            const pointerActive = now < pointer.activeUntil;

            if (pointerActive && dist < 320) {
                const proximity = 1 - dist / 320;
                const follow = proximity * proximity;
                const dampBoost = dist < 120 ? 0.11 : 0.03;
                targetX += clamp(dx * 0.07 * follow, -33, 33);
                targetY += clamp(dy * 0.07 * follow, -33, 33);
                state.vx *= 1 - dampBoost;
                state.vy *= 1 - dampBoost;
            }

            const spring = 0.16;
            const damping = 0.18;
            const ax = (targetX - state.x) * spring - state.vx * damping;
            const ay = (targetY - state.y) * spring - state.vy * damping;
            state.vx += ax * dt;
            state.vy += ay * dt;
            state.x += state.vx * dt;
            state.y += state.vy * dt;

            const d = Math.hypot(state.x, state.y);
            if (d > radius) {
                const scale = radius / d;
                state.x *= scale;
                state.y *= scale;
                state.vx *= 0.72;
                state.vy *= 0.72;
            }

            octoFab.style.transform = `translate(${state.x.toFixed(2)}px, ${state.y.toFixed(2)}px)`;
            if (octoCreature) {
                const tilt = clamp(state.vx * 2.4, -8, 8);
                octoCreature.style.transform = `rotate(${tilt.toFixed(2)}deg)`;
            }
            window.requestAnimationFrame(tick);
        };

        window.requestAnimationFrame(tick);
    }

    function runPostLoginTransition() {
        if (!octoFab) return;
        const flag = window.sessionStorage.getItem('ocean_login_transition');
        if (flag !== '1') return;
        window.sessionStorage.removeItem('ocean_login_transition');

        if (appMainContent) {
            const overlay = document.createElement('div');
            overlay.className = 'dashboard-transition-overlay';
            appMainContent.appendChild(overlay);
            requestAnimationFrame(() => {
                overlay.classList.add('fade-out');
            });
            window.setTimeout(() => overlay.remove(), 780);
        }

        octoFab.classList.add('from-login');
        requestAnimationFrame(() => {
            octoFab.classList.add('settle');
        });
        window.setTimeout(() => {
            octoFab.classList.remove('from-login', 'settle');
        }, 900);
    }

    function appendMsg(sender, text, id) {
        const container = document.getElementById('chat-messages');
        const wrapper = document.createElement('div');
        wrapper.className = sender === 'user' ? 'user-msg' : 'ai-msg';
        if (id) wrapper.id = id;

        const bubble = document.createElement('div');
        bubble.textContent = text;
        wrapper.appendChild(bubble);
        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }

    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const query = input.value.trim();
        if (!query) return;

        appendMsg('user', query);
        input.value = '';
        const loadingId = `ai-${Date.now()}`;
        appendMsg('ai', 'Thinking...', loadingId);

        try {
            const response = await fetch(config.dataset.chatUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || '',
                },
                body: JSON.stringify({ query }),
            });
            const data = await response.json();
            const loadingNode = document.getElementById(loadingId);
            if (loadingNode) loadingNode.remove();
            if (data.message) {
                appendMsg('ai', data.message);
                if (data.type === 'record') setTimeout(() => window.location.reload(), 2000);
            }
        } catch (e) {
            const loadingNode = document.getElementById(loadingId);
            if (loadingNode) loadingNode.innerText = 'Server error.';
        }
    }

    const labels = chartLabelsEl ? JSON.parse(chartLabelsEl.textContent) : [];
    const chartData = chartDataEl ? JSON.parse(chartDataEl.textContent) : [];
    if (labels.length === 0) {
        chartCanvasEl.style.display = 'none';
        chartHintEl.textContent = 'No expense data for this period.';
    } else {
        const isSingleCategory = labels.length === 1;
        chartHintEl.textContent = isSingleCategory
            ? `All current expenses are in "${labels[0]}".`
            : `${labels.length} categories in this period.`;

        new Chart(chartCanvasEl, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: chartData,
                    backgroundColor: ['#38bdf8', '#0ea5e9', '#22d3ee', '#2dd4bf', '#34d399'],
                    hoverOffset: 4,
                }],
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
            },
        });
    }

    resetDateTime();

    document.getElementById('openAddModalBtn').addEventListener('click', openAddModal);
    document.querySelectorAll('.edit-transaction-btn').forEach((btn) => {
        btn.addEventListener('click', () => openEditModal(btn.dataset.transactionId));
    });
    document.querySelectorAll('.chat-toggle-btn').forEach((btn) => {
        btn.addEventListener('click', toggleChat);
    });
    document.getElementById('chat-send-btn').addEventListener('click', sendMessage);
    document.getElementById('chat-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && chatOpen) {
            applyChatState(false);
        }
    });
    document.querySelectorAll('.confirm-delete-form').forEach((form) => {
        form.addEventListener('submit', (e) => {
            if (!window.confirm('Are you sure you want to delete this record?')) {
                e.preventDefault();
            }
        });
    });
    bindFabEyeTracking();
    bindFabPhysics();
    runPostLoginTransition();
    applyChatState(false);
});
