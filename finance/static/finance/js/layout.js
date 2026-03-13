document.addEventListener('DOMContentLoaded', () => {
    const storageKey = 'tango_sidebar_collapsed';

    function initSidebarToggle() {
        const btn = document.getElementById('sidebarToggleBtn');
        if (!btn) return;
        const icon = btn.querySelector('i');

        function updateIcon() {
            const collapsed = document.body.classList.contains('sidebar-collapsed');
            if (!icon) return;
            icon.className = collapsed ? 'bi bi-chevron-right' : 'bi bi-chevron-left';
        }

        const saved = window.localStorage.getItem(storageKey);
        if (saved === '1') {
            document.body.classList.add('sidebar-collapsed');
        }
        updateIcon();

        btn.addEventListener('click', () => {
            document.body.classList.toggle('sidebar-collapsed');
            const collapsed = document.body.classList.contains('sidebar-collapsed');
            window.localStorage.setItem(storageKey, collapsed ? '1' : '0');
            updateIcon();
        });
    }

    function createTransitionOverlay() {
        let overlay = document.querySelector('.page-transition-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'page-transition-overlay';
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    function isInternalNavigableLink(anchor) {
        if (!anchor || !anchor.href) return false;
        if (anchor.target && anchor.target.toLowerCase() === '_blank') return false;
        if (anchor.hasAttribute('download')) return false;
        if (anchor.dataset.noTransition === 'true') return false;
        if (anchor.getAttribute('href').startsWith('#')) return false;
        if (anchor.getAttribute('href').startsWith('javascript:')) return false;
        if (anchor.getAttribute('href').startsWith('mailto:')) return false;
        if (anchor.getAttribute('href').startsWith('tel:')) return false;
        if (anchor.hasAttribute('data-bs-toggle')) return false;
        const url = new URL(anchor.href, window.location.origin);
        if (url.origin !== window.location.origin) return false;
        if (url.pathname === window.location.pathname && url.search === window.location.search && url.hash) return false;
        return true;
    }

    function initPageTransitions() {
        const overlay = createTransitionOverlay();
        overlay.classList.add('enter');
        window.requestAnimationFrame(() => {
            overlay.classList.add('enter-active');
            window.setTimeout(() => {
                overlay.classList.remove('enter', 'enter-active');
            }, 380);
        });

        let leaving = false;
        document.addEventListener('click', (evt) => {
            const anchor = evt.target.closest('a');
            if (!anchor) return;
            if (evt.defaultPrevented) return;
            if (evt.metaKey || evt.ctrlKey || evt.shiftKey || evt.altKey || evt.button !== 0) return;
            if (!isInternalNavigableLink(anchor)) return;
            if (leaving) return;

            evt.preventDefault();
            leaving = true;
            const to = anchor.href;
            document.body.classList.add('page-leaving');
            overlay.classList.add('leave');
            window.setTimeout(() => {
                window.location.assign(to);
            }, 300);
        }, true);
    }

    initSidebarToggle();
    initPageTransitions();
});
