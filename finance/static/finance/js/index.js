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
    const transactionModalDialog = transactionModalEl ? transactionModalEl.querySelector('.modal-dialog') : null;
    let modalBackdropEl = null;
    const transactionForm = document.getElementById('transactionForm');
    const modalTitle = document.getElementById('modalTitle');
    const submitBtn = document.getElementById('submitBtn');
    const chatWindow = document.getElementById('chat-window');
    const chartLabelsEl = document.getElementById('chart-labels');
    const chartDataEl = document.getElementById('chart-data');
    const siteSearchItemsEl = document.getElementById('site-search-items');
    const chartHintEl = document.getElementById('expenseChartHint');
    const chartCanvasEl = document.getElementById('expenseChart');
    const siteSearchForm = document.getElementById('site-search-form');
    const siteSearchInput = document.getElementById('site-search-input');
    const fabPupils = document.querySelectorAll('.octo-pupil');
    const octoFab = document.querySelector('.octo-fab');
    const octoCreature = document.querySelector('.octo-fab-creature');
    const appMainContent = document.querySelector('.app-main-content');
    let chatOpen = false;
    const siteSearchItems = siteSearchItemsEl ? JSON.parse(siteSearchItemsEl.textContent) : [];
    const topMenus = document.querySelectorAll('[data-menu]');
    let expenseChartInstance = null;

    if (topMenus.length) {
        const closeMenu = (menu) => {
            menu.removeAttribute('open');
            menu.classList.remove('is-open');
            const toggle = menu.querySelector('[data-menu-toggle]');
            if (toggle) toggle.setAttribute('aria-expanded', 'false');
        };
        const openMenu = (menu) => {
            menu.classList.add('is-open');
            const toggle = menu.querySelector('[data-menu-toggle]');
            if (toggle) toggle.setAttribute('aria-expanded', 'true');
        };

        document.addEventListener('click', (event) => {
            const toggleBtn = event.target.closest('[data-menu-toggle]');
            if (toggleBtn) {
                const menu = toggleBtn.closest('[data-menu]');
                const willOpen = menu && !menu.classList.contains('is-open');
                topMenus.forEach((node) => closeMenu(node));
                if (menu && willOpen) openMenu(menu);
                return;
            }
            topMenus.forEach((menu) => {
                if (!menu.contains(event.target)) closeMenu(menu);
            });
        });

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                topMenus.forEach((menu) => closeMenu(menu));
            }
        });
    }

    function clamp(value, min, max) {
        return Math.max(min, Math.min(max, value));
    }

    function resetDateTime() {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        document.getElementById('datetime_now').value = now.toISOString().slice(0, 16);
    }

    function showTransactionModal() {
        if (!transactionModalEl) return;
        transactionModalEl.classList.add('show', 'manual-modal-open');
        transactionModalEl.style.display = 'block';
        transactionModalEl.removeAttribute('aria-hidden');
        transactionModalEl.setAttribute('aria-modal', 'true');

        if (!modalBackdropEl) {
            modalBackdropEl = document.createElement('div');
            modalBackdropEl.className = 'modal-backdrop fade show manual-modal-backdrop';
            document.body.appendChild(modalBackdropEl);
            modalBackdropEl.addEventListener('click', hideTransactionModal);
        }
        document.body.classList.add('modal-open');
    }

    function hideTransactionModal() {
        if (!transactionModalEl) return;
        transactionModalEl.classList.remove('show', 'manual-modal-open');
        transactionModalEl.style.display = 'none';
        transactionModalEl.setAttribute('aria-hidden', 'true');
        transactionModalEl.removeAttribute('aria-modal');

        if (modalBackdropEl) {
            modalBackdropEl.remove();
            modalBackdropEl = null;
        }
        document.body.classList.remove('modal-open');
    }

    function openAddModal() {
        transactionForm.reset();
        transactionForm.action = config.dataset.addUrl;
        modalTitle.innerText = 'New Transaction';
        submitBtn.innerText = 'Save Transaction';
        resetDateTime();
        showTransactionModal();
    }

    function openEditModal(tid) {
        modalTitle.innerText = 'Edit Transaction';
        submitBtn.innerText = 'Update Transaction';
        const editUrl = config.dataset.editTemplate.replace('0', tid);
        transactionForm.action = editUrl;

        fetch(editUrl)
            .then(async (response) => {
                const contentType = (response.headers.get('content-type') || '').toLowerCase();
                if (!contentType.includes('application/json')) {
                    throw new Error('Session expired or unexpected server response. Please refresh and try again.');
                }
                const payload = await response.json();
                if (!response.ok) {
                    throw new Error(payload.message || 'Failed to load transaction');
                }
                return payload;
            })
            .then((data) => {
                transactionForm.querySelector('[name="amount"]').value = data.amount;
                transactionForm.querySelector('[name="currency"]').value = data.currency;
                transactionForm.querySelector('[name="type"]').value = data.type;
                transactionForm.querySelector('[name="category"]').value = data.category;
                transactionForm.querySelector('[name="date"]').value = data.date;
                transactionForm.querySelector('[name="note"]').value = data.note;
                showTransactionModal();
            })
            .catch((error) => alert(error.message || 'Error fetching data.'));
    }

    function applyChatState(nextOpen) {
        chatOpen = nextOpen;
        chatWindow.classList.toggle('chat-window-open', chatOpen);
        chatWindow.classList.toggle('chat-window-closed', !chatOpen);
        chatWindow.setAttribute('aria-hidden', chatOpen ? 'false' : 'true');
        window.sessionStorage.setItem('ocean_chat_open', chatOpen ? '1' : '0');

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

    function normalizeQuery(text) {
        return (text || '').toLowerCase().trim();
    }

    function performSiteSearch(rawQuery) {
        const query = normalizeQuery(rawQuery);
        if (!query) return;

        const direct = siteSearchItems.find((entry) => normalizeQuery(entry.value) === query);
        if (direct) {
            window.location.href = direct.target;
            return;
        }
        const partial = siteSearchItems.find((entry) =>
            normalizeQuery(entry.value).includes(query) || normalizeQuery(entry.label).includes(query)
        );
        if (partial) {
            window.location.href = partial.target;
            return;
        }
        window.alert('No matching feature found. Try: profile, delete account, transactions.');
    }

    function buildChartPalette(count) {
        const base = [
            '#22d3ee', '#38bdf8', '#2dd4bf', '#34d399', '#60a5fa', '#818cf8',
            '#a78bfa', '#f472b6', '#fb7185', '#f59e0b', '#84cc16', '#14b8a6',
        ];
        if (count <= base.length) return base.slice(0, count);
        const colors = [...base];
        for (let i = base.length; i < count; i += 1) {
            const hue = Math.round((i * 137.508) % 360);
            colors.push(`hsl(${hue} 78% 56%)`);
        }
        return colors;
    }

    function formatGBP(value) {
        return new Intl.NumberFormat('en-GB', {
            style: 'currency',
            currency: 'GBP',
            maximumFractionDigits: 2,
            minimumFractionDigits: 2,
        }).format(value);
    }


    function formatAmountWithSign(value, type, currency) {
        const amount = Number(value) || 0;
        const sign = type === 'Income' ? '+' : '-';
        return `${sign}${currency} ${amount.toFixed(2)}`;
    }

    function escapeHtml(input) {
        return String(input ?? '')
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    function updateMetricBlocks(metrics) {
        const monthIncome = document.getElementById('month-income-value');
        const monthExpense = document.getElementById('month-expense-value');
        const monthNet = document.getElementById('month-net-value');
        const kpiExpense = document.getElementById('kpi-expense-value');
        const kpiIncome = document.getElementById('kpi-income-value');
        const kpiNet = document.getElementById('kpi-net-value');
        const kpiExpenseProgress = document.getElementById('kpi-expense-progress');
        const kpiIncomeProgress = document.getElementById('kpi-income-progress');

        if (monthIncome) monthIncome.textContent = formatGBP(metrics.month_income || 0);
        if (monthExpense) monthExpense.textContent = formatGBP(metrics.month_expense || 0);
        if (monthNet) monthNet.textContent = formatGBP(metrics.month_net || 0);
        if (kpiExpense) kpiExpense.textContent = formatGBP(metrics.month_expense || 0);
        if (kpiIncome) kpiIncome.textContent = formatGBP(metrics.month_income || 0);
        if (kpiNet) kpiNet.textContent = formatGBP(metrics.month_net || 0);
        if (kpiExpenseProgress) kpiExpenseProgress.style.width = `${metrics.expense_progress || 0}%`;
        if (kpiIncomeProgress) kpiIncomeProgress.style.width = `${metrics.income_progress || 0}%`;
    }

    function buildChartHint(labels, values) {
        const hintEl = document.getElementById('expenseChartHint');
        if (!hintEl) return;
        const total = values.reduce((sum, v) => sum + (Number(v) || 0), 0);
        if (!labels.length || total <= 0) {
            hintEl.textContent = 'No expense data for this period.';
            return;
        }
        if (labels.length === 1) {
            hintEl.textContent = `All current expenses are in "${labels[0]}".`;
            return;
        }
        let topIndex = 0;
        for (let i = 1; i < values.length; i += 1) {
            if ((Number(values[i]) || 0) > (Number(values[topIndex]) || 0)) topIndex = i;
        }
        const topValue = Number(values[topIndex]) || 0;
        const share = total > 0 ? (topValue / total) * 100 : 0;
        hintEl.textContent = `Top category: ${labels[topIndex]} (${share.toFixed(1)}%).`;
    }

    function upsertLatestTransactionRow(transaction) {
        const tbody = document.getElementById('transaction-table-body');
        if (!tbody || !transaction) return;

        const existing = tbody.querySelector('.empty-transactions-row');
        if (existing) existing.remove();

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <div class="fw-semibold">${escapeHtml(transaction.note)}</div>
                <div class="small text-light-emphasis">${escapeHtml(transaction.occurred_at_short)}</div>
            </td>
            <td>
                <span class="badge category-pill ${transaction.type === 'Income' ? 'income-pill' : 'expense-pill'}">
                    ${escapeHtml(transaction.category_name)}
                </span>
            </td>
            <td>${escapeHtml(transaction.occurred_at_full)}</td>
            <td class="text-end ${transaction.type === 'Income' ? 'amount-pos' : 'amount-neg'}">
                ${escapeHtml(formatAmountWithSign(transaction.original_amount, transaction.type, transaction.currency))}
            </td>
            <td class="text-end">£ ${Number(transaction.amount_in_gbp || 0).toFixed(2)}</td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-outline-info border-0 edit-transaction-btn" data-transaction-id="${transaction.id}" type="button">
                        <i class="bi bi-pencil-square"></i>
                    </button>
                    <form action="${transaction.delete_url}" method="post" class="d-inline confirm-delete-form">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${getCookie('csrftoken') || ''}">
                        <button type="submit" class="btn btn-sm btn-outline-danger border-0">
                            <i class="bi bi-trash"></i>
                        </button>
                    </form>
                </div>
            </td>
        `;
        tbody.prepend(tr);

        const editBtn = tr.querySelector('.edit-transaction-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => openEditModal(String(transaction.id)));
        }
        const deleteForm = tr.querySelector('.confirm-delete-form');
        if (deleteForm) {
            deleteForm.addEventListener('submit', (e) => {
                if (!window.confirm('Are you sure you want to delete this record?')) {
                    e.preventDefault();
                }
            });
        }
    }

    async function refreshDashboardState(transactionPayload) {
        const stateUrl = config.dataset.dashboardStateUrl;
        if (!stateUrl) return;
        try {
            const response = await fetch(stateUrl, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            if (!response.ok) return;
            const payload = await response.json();
            if (payload.status !== 'success') return;

            updateMetricBlocks(payload.metrics || {});
            buildChartHint(payload.chart?.labels || [], payload.chart?.data || []);

            if (expenseChartInstance && payload.chart) {
                expenseChartInstance.data.labels = payload.chart.labels || [];
                expenseChartInstance.data.datasets[0].data = (payload.chart.data || []).map((v) => Number(v) || 0);
                expenseChartInstance.update();
            }

            const resultCount = document.getElementById('result-count-text');
            if (resultCount && typeof payload.total_count === 'number') {
                const plural = payload.total_count === 1 ? '' : 's';
                resultCount.textContent = `${payload.total_count} result${plural} matched your filters`;
            }
        } catch (_err) {
            // Keep UX resilient: if refresh fails, chat still succeeds.
        }

        if (transactionPayload) {
            upsertLatestTransactionRow(transactionPayload);
        }
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
            if (!response.ok || data.status === 'error') {
                appendMsg('ai', data.message || 'Request failed. Please retry.');
                return;
            }
            if (data.message) {
                appendMsg('ai', data.message);
            }
            if (data.type === 'record') {
                await refreshDashboardState(data.transaction);
            }
        } catch (e) {
            const loadingNode = document.getElementById(loadingId);
            if (loadingNode) loadingNode.innerText = 'Server error.';
        }
    }

    const labels = chartLabelsEl ? JSON.parse(chartLabelsEl.textContent) : [];
    const chartData = chartDataEl ? JSON.parse(chartDataEl.textContent).map((v) => Number(v) || 0) : [];
    const totalExpense = chartData.reduce((sum, value) => sum + value, 0);

    if (labels.length === 0 || totalExpense <= 0 || typeof Chart === 'undefined') {
        chartCanvasEl.style.display = 'none';
        chartHintEl.textContent = 'No expense data for this period.';
    } else {
        const isSingleCategory = labels.length === 1;
        if (isSingleCategory) {
            chartHintEl.textContent = `All current expenses are in "${labels[0]}".`;
        } else {
            let topIndex = 0;
            for (let i = 1; i < chartData.length; i += 1) {
                if (chartData[i] > chartData[topIndex]) topIndex = i;
            }
            const share = (chartData[topIndex] / totalExpense) * 100;
            chartHintEl.textContent = `Top category: ${labels[topIndex]} (${share.toFixed(1)}%).`;
        }

        const palette = buildChartPalette(labels.length);

        expenseChartInstance = new Chart(chartCanvasEl, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: chartData,
                    backgroundColor: palette,
                    borderColor: 'rgba(10, 28, 35, 0.95)',
                    borderWidth: 2,
                    hoverOffset: 8,
                }],
            },
            options: {
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom',
                        labels: {
                            color: '#b7d3dc',
                            usePointStyle: true,
                            pointStyle: 'circle',
                            boxWidth: 10,
                            boxHeight: 10,
                            padding: 14,
                            font: {
                                size: 11,
                                weight: '600',
                            },
                        },
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                const value = Number(context.parsed) || 0;
                                const percentage = totalExpense > 0 ? ((value / totalExpense) * 100) : 0;
                                return `${context.label}: ${formatGBP(value)} (${percentage.toFixed(1)}%)`;
                            },
                        },
                    },
                },
                onHover(event, activeElements) {
                    event.native.target.style.cursor = activeElements.length ? 'pointer' : 'default';
                },
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
        if (e.key === 'Escape' && transactionModalEl && transactionModalEl.classList.contains('manual-modal-open')) {
            hideTransactionModal();
        }
        if (e.key === 'Escape' && chatOpen) {
            applyChatState(false);
        }
    });
    if (transactionModalEl) {
        transactionModalEl.querySelectorAll('[data-bs-dismiss="modal"]').forEach((btn) => {
            btn.addEventListener('click', hideTransactionModal);
        });
        transactionModalEl.addEventListener('click', (event) => {
            if (event.target === transactionModalEl) {
                hideTransactionModal();
            }
        });
    }
    if (transactionModalDialog) {
        transactionModalDialog.addEventListener('click', (event) => {
            event.stopPropagation();
        });
    }
    document.querySelectorAll('.confirm-delete-form').forEach((form) => {
        form.addEventListener('submit', (e) => {
            if (!window.confirm('Are you sure you want to delete this record?')) {
                e.preventDefault();
            }
        });
    });
    if (siteSearchForm && siteSearchInput) {
        siteSearchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            performSiteSearch(siteSearchInput.value);
        });
        siteSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                performSiteSearch(siteSearchInput.value);
            }
        });
        siteSearchInput.addEventListener('change', () => {
            performSiteSearch(siteSearchInput.value);
        });
    }
    const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const enableHeavyFabMotion = !prefersReducedMotion && window.innerWidth >= 992;
    if (enableHeavyFabMotion) {
        bindFabEyeTracking();
        bindFabPhysics();
    }
    runPostLoginTransition();
    applyChatState(window.sessionStorage.getItem('ocean_chat_open') === '1');
});
