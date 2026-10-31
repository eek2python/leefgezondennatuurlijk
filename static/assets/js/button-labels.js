/* Keep product actions readable on narrow screens, including enlarged text.
   This changes presentation only, never destinations or link classifications. */
(function () {
    'use strict';
    var main = document.getElementById('main');
    if (!main) return;
    var states = new WeakMap();
    var mobile = window.matchMedia('(max-width: 736px)');
    var context = document.createElement('canvas').getContext('2d');
    var pending = false;

    function update() {
        pending = false;
        main.querySelectorAll('.button[data-link-type], .button.disabled').forEach(function (button) {
            var text = button.textContent.trim();
            var state = states.get(button);
            if (!state || text !== state.rendered) {
                state = {full: text, rendered: text};
                states.set(button, state);
            }
            var label = state.full;
            if (mobile.matches && button.getClientRects().length && context) {
                var style = getComputedStyle(button);
                context.font = style.fontWeight + ' ' + style.fontSize + ' ' + style.fontFamily;
                var available = button.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
                if (context.measureText(label).width > available + 1) {
                    var type = button.getAttribute('data-link-type');
                    if (type === 'affiliate' || type === 'retailer') {
                        label = label.replace(/prijs (?:en|&) reviews/i, 'prijs');
                        if (context.measureText(label).width > available + 1)
                            label = 'Bekijk prijs →';
                    } else if (type === 'official') {
                        label = 'Productinformatie →';
                        if (context.measureText(label).width > available + 1)
                            label = 'Specificaties →';
                    } else if (button.classList.contains('disabled')) {
                        label = 'Niet beschikbaar';
                        if (context.measureText(label).width > available + 1)
                            label = 'Geen link';
                    }
                }
            }
            if (button.textContent.trim() !== label) {
                if (!button.hasAttribute('aria-label'))
                    button.setAttribute('aria-label', state.full);
                state.rendered = label;
                button.textContent = label;
            }
        });
    }
    function schedule() {
        if (!pending) {
            pending = true;
            requestAnimationFrame(update);
        }
    }
    new MutationObserver(schedule).observe(main, {
        subtree: true, childList: true, characterData: true,
        attributes: true, attributeFilter: ['data-link-type', 'hidden']
    });
    if ('ResizeObserver' in window) {
        var observer = new ResizeObserver(schedule);
        observer.observe(main);
        main.querySelectorAll('.button').forEach(function (button) { observer.observe(button); });
    }
    window.addEventListener('resize', schedule);
    if (document.fonts) document.fonts.ready.then(schedule);
    update();
})();
