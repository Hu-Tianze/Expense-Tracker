function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function handleOtpRequest(btnId, statusId, url, modalId) {
    const btn = document.getElementById(btnId);
    const status = document.getElementById(statusId);
    const tokenField = document.querySelector(`#${modalId} [name="cf-turnstile-response"]`);
    const hasTurnstileWidget = !!tokenField;
    const turnstileResponse = tokenField ? tokenField.value : '';

    const config = document.getElementById('profile-config');
    const turnstileEnabled = config && config.dataset.turnstileEnabled === '1';

    if (turnstileEnabled && hasTurnstileWidget && !turnstileResponse) {
        alert('Please complete the security check first!');
        return;
    }

    btn.disabled = true;
    status.innerText = 'Sending...';
    status.className = 'small text-muted';

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken') || '',
        },
        body: `cf_token=${encodeURIComponent(turnstileResponse)}`,
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.status === 'success') {
                status.innerText = 'Code sent!';
                status.className = 'small text-success';
                let count = 60;
                const timer = setInterval(() => {
                    count -= 1;
                    btn.innerText = `Wait (${count}s)`;
                    if (count <= 0) {
                        clearInterval(timer);
                        btn.disabled = false;
                        btn.innerText = 'Get Code';
                    }
                }, 1000);
            } else {
                status.innerText = data.message;
                status.className = 'small text-danger';
                btn.disabled = false;
                if (typeof turnstile !== 'undefined') turnstile.reset();
            }
        })
        .catch(() => {
            status.innerText = 'Error occurred.';
            btn.disabled = false;
        });
}

document.addEventListener('DOMContentLoaded', () => {
    const config = document.getElementById('profile-config');
    if (!config) return;
    const topMenus = document.querySelectorAll('.profile-top-menu');
    const profileForm = document.getElementById('profileForm');
    const stickyBar = document.getElementById('profileStickyBar');
    const cancelBtn = document.getElementById('profileCancelBtn');

    const sendPwdBtn = document.getElementById('btnSendPwdOTP');
    const sendDeleteBtn = document.getElementById('btnSendDeleteOTP');

    sendPwdBtn.addEventListener('click', () => {
        handleOtpRequest('btnSendPwdOTP', 'pwdOtpStatus', config.dataset.sendPwdUrl, 'changePasswordModal');
    });

    sendDeleteBtn.addEventListener('click', () => {
        handleOtpRequest('btnSendDeleteOTP', 'otpStatus', config.dataset.sendDeleteUrl, 'deleteAccountModal');
    });

    document.querySelectorAll('.confirm-category-delete-form').forEach((form) => {
        form.addEventListener('submit', (e) => {
            if (!window.confirm('Delete category?')) {
                e.preventDefault();
            }
        });
    });

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
                const menu = toggleBtn.closest('.profile-top-menu');
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

    if (profileForm && stickyBar) {
        const controls = Array.from(profileForm.querySelectorAll('input, select, textarea'))
            .filter((el) => !el.disabled);
        const initialValues = new Map(controls.map((el) => [el.name || el.id, el.value]));

        const isDirty = () => controls.some((el) => initialValues.get(el.name || el.id) !== el.value);
        const refreshSticky = () => {
            if (isDirty()) {
                stickyBar.classList.remove('profile-sticky-hidden');
            } else {
                stickyBar.classList.add('profile-sticky-hidden');
            }
        };

        controls.forEach((el) => {
            el.addEventListener('input', refreshSticky);
            el.addEventListener('change', refreshSticky);
        });

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                controls.forEach((el) => {
                    el.value = initialValues.get(el.name || el.id) || '';
                });
                refreshSticky();
            });
        }
        refreshSticky();
    }
});
