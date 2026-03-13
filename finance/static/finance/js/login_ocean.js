document.addEventListener('DOMContentLoaded', () => {
    const pupils = document.querySelectorAll('.octo-pupil');
    const eyes = document.querySelectorAll('.octo-eye');
    const form = document.getElementById('loginForm');
    const loginOcto = document.getElementById('loginOcto');
    const inlineError = document.getElementById('loginInlineError');

    const maxOffset = 8;

    function movePupil(eye, pupil, clientX, clientY) {
        const rect = eye.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        const dx = clientX - cx;
        const dy = clientY - cy;
        const angle = Math.atan2(dy, dx);
        const distance = Math.min(maxOffset, Math.hypot(dx, dy) / 14);
        const x = Math.cos(angle) * distance;
        const y = Math.sin(angle) * distance;
        pupil.style.transform = `translate(${x}px, ${y}px)`;
    }

    if (pupils.length && eyes.length) {
        const onMove = (evt) => {
            const x = evt.clientX;
            const y = evt.clientY;
            eyes.forEach((eye, idx) => movePupil(eye, pupils[idx], x, y));
        };

        window.addEventListener('mousemove', onMove, { passive: true });
        window.addEventListener('touchmove', (evt) => {
            const touch = evt.touches && evt.touches[0];
            if (!touch) return;
            onMove({ clientX: touch.clientX, clientY: touch.clientY });
        }, { passive: true });
    }

    if (!form || !loginOcto) return;

    function playLoginErrorReaction() {
        loginOcto.classList.remove('error-react');
        void loginOcto.offsetWidth;
        loginOcto.classList.add('error-react');
        window.setTimeout(() => {
            loginOcto.classList.remove('error-react');
        }, 620);
    }

    if (form.dataset.hasErrors === '1') {
        if (inlineError) inlineError.classList.add('show');
        playLoginErrorReaction();
    }

    const passwordInput = document.getElementById('id_password');
    if (passwordInput && inlineError) {
        passwordInput.addEventListener('input', () => {
            inlineError.classList.remove('show');
        });
    }

    let animating = false;
    form.addEventListener('submit', (evt) => {
        if (animating) return;
        if (!form.checkValidity()) return;

        evt.preventDefault();
        animating = true;

        const source = loginOcto.getBoundingClientRect();
        const clone = loginOcto.cloneNode(true);
        clone.classList.add('octo-transition-clone');
        clone.style.left = `${source.left}px`;
        clone.style.top = `${source.top}px`;
        clone.style.width = `${source.width}px`;
        clone.style.height = `${source.height}px`;
        document.body.appendChild(clone);

        loginOcto.style.opacity = '0';
        document.body.classList.add('login-transitioning');

        const targetX = window.innerWidth - 72;
        const targetY = window.innerHeight - 72;
        const centerX = source.left + source.width / 2;
        const centerY = source.top + source.height / 2;
        const dx = targetX - centerX;
        const dy = targetY - centerY;

        requestAnimationFrame(() => {
            clone.style.transform = `translate(${dx}px, ${dy}px) scale(0.24)`;
            clone.style.opacity = '0.92';
        });

        window.sessionStorage.setItem('ocean_login_transition', '1');

        window.setTimeout(() => {
            form.submit();
        }, 620);
    });
});
