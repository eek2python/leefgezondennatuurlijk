/* Shared presentation helpers; product selection and destinations stay untouched. */
(function () {
    'use strict';
    var root = document.documentElement;
    var bars = Array.from(document.querySelectorAll('.format-sticky, .storage-filters-sticky'));
    var pending;
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
        // The format bar now shares the menu row; storage filters remain below it.
        var mobile = window.matchMedia('(max-width: 1280px)').matches;
        var storage = bars.some(function (bar) {
            return bar.classList.contains('storage-filters-sticky') &&
                bar.classList.contains('is-stuck') && !bar.classList.contains('is-too-tall');
        });
        root.style.setProperty('--sticky-filter-height', (height + (mobile && storage ? 56 : 0)) + 'px');
    }
    function revealHash() {
        if (!location.hash) return;
        var target;
        try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
        catch (error) { return; }
        if (!target) return;
        // Wait until scroll-triggered filter visibility and wrapping have settled.
        clearTimeout(pending);
        pending = setTimeout(function () {
            updateOffset();
            target.scrollIntoView({block: 'start'});
        }, 180);
    }
    bars.forEach(function (bar) {
        new MutationObserver(updateOffset).observe(bar, {attributes: true, attributeFilter: ['class']});
        if ('ResizeObserver' in window) new ResizeObserver(updateOffset).observe(bar);
    });
    window.addEventListener('hashchange', revealHash);
    window.addEventListener('resize', function () { updateOffset(); revealHash(); });
    window.addEventListener('load', revealHash);
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
