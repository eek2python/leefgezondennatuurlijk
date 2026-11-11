/* Shared presentation helpers; product selection and destinations stay untouched. */
(function () {
    'use strict';
    var root = document.documentElement;
    var bars = Array.from(document.querySelectorAll('.format-sticky, .storage-filters-sticky'));
    var pending;
    var userNavigation = 0;
    function cancelPendingReveal() {
        userNavigation++;
        clearTimeout(pending);
    }
    // A late load event must not undo scrolling the visitor already started.
    window.addEventListener('wheel', cancelPendingReveal, {passive: true});
    window.addEventListener('touchmove', cancelPendingReveal, {passive: true});
    window.addEventListener('keydown', function (event) {
        if (['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '].indexOf(event.key) !== -1)
            cancelPendingReveal();
    });
    function updateOffset() {
        var height = 0;
        bars.forEach(function (bar) {
            // On a short/zoomed screen a large storage filter must scroll
            // away normally rather than occupy most of the usable viewport.
            var tooTall = bar.getBoundingClientRect().height > window.innerHeight * 0.45;
            if (bar.classList.contains('is-too-tall') !== tooTall) {
                bar.classList.toggle('is-too-tall', tooTall);
            }
            if (!tooTall && (bar.classList.contains('is-visible') || bar.classList.contains('is-stuck'))) {
                height = Math.max(height, bar.getBoundingClientRect().height);
            }
        });
        // Both filter bars share the menu row instead of starting below it.
        root.style.setProperty('--sticky-filter-height', height + 'px');
    }
    function revealHash() {
        if (!location.hash) return;
        var target;
        try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
        catch (error) { return; }
        if (!target) return;
        var navigationAtRequest = userNavigation;
        // Wait until scroll-triggered filter visibility and wrapping have settled.
        clearTimeout(pending);
        pending = setTimeout(function () {
            if (navigationAtRequest !== userNavigation) return;
            updateOffset();
            target.scrollIntoView({block: 'start'});
        }, 180);
    }
    bars.forEach(function (bar) {
        new MutationObserver(updateOffset).observe(bar, {attributes: true, attributeFilter: ['class']});
        if ('ResizeObserver' in window) new ResizeObserver(updateOffset).observe(bar);
    });
    window.addEventListener('hashchange', revealHash);
    // Mobile browser chrome changes viewport height while scrolling. Recompute
    // filter offsets, but never treat a resize as a request to revisit the hash.
    window.addEventListener('resize', updateOffset);
    window.addEventListener('load', function () {
        if (userNavigation === 0) revealHash();
    });
    updateOffset();

    document.querySelectorAll('.table-wrapper').forEach(function (wrapper, index) {
        if (!wrapper.querySelector('table')) return;
        var hint = document.createElement('p');
        hint.className = 'table-scroll-hint';
        hint.id = 'table-scroll-hint-' + index;
        hint.textContent = 'Veeg horizontaal voor alle kolommen. Met het toetsenbord: gebruik de pijltjestoetsen.';
        wrapper.before(hint);
        wrapper.setAttribute('tabindex', '0');
        wrapper.setAttribute('role', 'region');
        if (!wrapper.hasAttribute('aria-label')) wrapper.setAttribute('aria-label', 'Vergelijkingstabel');
        wrapper.setAttribute('aria-describedby', hint.id);
        function updateHint() {
            hint.hidden = wrapper.scrollWidth <= wrapper.clientWidth + 1;
        }
        if ('ResizeObserver' in window) new ResizeObserver(updateHint).observe(wrapper);
        updateHint();
    });
})();
