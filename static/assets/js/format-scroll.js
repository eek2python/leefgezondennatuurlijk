/* Keep selections reachable and show when more options are available. */
(function () {
    'use strict';
    var mobile = window.matchMedia('(max-width: 1280px)');
    var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    document.querySelectorAll('.format-sticky').forEach(function (bar, index) {
        var chips = bar.querySelector('.format-sticky-chips');
        var inner = bar.querySelector('.format-sticky-inner');
        if (!chips || !inner) return;
        var isMaterial = bar.hasAttribute('data-material-sticky');
        var reference = document.querySelector(isMaterial ? '[data-material-selector]' :
            (bar.hasAttribute('data-size-sticky') ? '[data-size-selector]' : '[data-format-selector]'));
        // IntersectionObserver can miss a jump from below to above the viewport
        // when the selector never intersects between the two rendered frames.
        var scrollPending = false;
        function syncVisibility() {
            scrollPending = false;
            if (!reference) return;
            // On phones the material choices have left the usable area once
            // they pass behind the shared menu row.
            var visible = reference.getBoundingClientRect().bottom <= (isMaterial && mobile.matches ? 56 : 0);
            if (bar.classList.contains('is-visible') !== visible)
                bar.classList.toggle('is-visible', visible);
            bar.inert = !visible;
        }
        window.addEventListener('scroll', function () {
            if (!scrollPending) {
                scrollPending = true;
                requestAnimationFrame(syncVisibility);
            }
        }, {passive: true});
        chips.id = chips.id || 'sticky-format-options-' + index;

        function makeButton(label, glyph, direction) {
            var button = document.createElement('button');
            button.type = 'button';
            button.className = 'format-scroll-button';
            button.setAttribute('aria-label', label);
            button.setAttribute('aria-controls', chips.id);
            button.textContent = glyph;
            button.hidden = true;
            button.addEventListener('click', function () {
                chips.scrollBy({
                    left: direction * Math.max(80, chips.clientWidth * 0.75),
                    behavior: reducedMotion.matches ? 'auto' : 'smooth'
                });
            });
            return button;
        }
        var previous = makeButton(isMaterial ? 'Vorige materialen' : 'Vorige formaten', '‹', -1);
        var next = makeButton(isMaterial ? 'Meer materialen' : 'Meer formaten', '›', 1);
        inner.insertBefore(previous, chips);
        inner.appendChild(next);

        function update() {
            var style = getComputedStyle(inner);
            var available = inner.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
            var overflow = mobile.matches && chips.scrollWidth > available + 1;
            previous.hidden = next.hidden = !overflow;
            previous.disabled = chips.scrollLeft <= 1;
            next.disabled = chips.scrollLeft + chips.clientWidth >= chips.scrollWidth - 1;
        }
        function revealSelected() {
            if (mobile.matches) {
                var selected = chips.querySelector('[aria-current="page"], .is-active');
                if (selected) {
                    var item = selected.getBoundingClientRect();
                    var container = chips.getBoundingClientRect();
                    chips.scrollLeft += item.left - container.left - (container.width - item.width) / 2;
                }
            }
            update();
        }
        chips.addEventListener('scroll', update, {passive: true});
        window.addEventListener('resize', function () { syncVisibility(); update(); revealSelected(); });
        if ('ResizeObserver' in window) new ResizeObserver(update).observe(inner);
        new MutationObserver(function () {
            if (bar.classList.contains('is-visible')) {
                update();
                revealSelected();
            }
        }).observe(bar, {attributes: true, attributeFilter: ['class']});
        update();
        revealSelected();
        syncVisibility();
        if (document.fonts) document.fonts.ready.then(function () {
            update();
            revealSelected();
        });
    });
})();
