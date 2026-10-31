/* Reuse server-rendered content; normal URLs and tables remain the no-JS fallback. */
(function () {
    'use strict';
    var phone = window.matchMedia('(max-width: 736px)');
    var helps = Array.from(document.querySelectorAll('details.category-help'));
    var comparisons = [];

    function copyContents(source, target) {
        Array.from(source.childNodes).forEach(function (node) {
            target.appendChild(node.cloneNode(true));
        });
        // A cloned comparison must never introduce duplicate document IDs.
        target.querySelectorAll('[id]').forEach(function (element) {
            element.removeAttribute('id');
        });
    }

    document.querySelectorAll('.table-wrapper table.product-table').forEach(function (table, index) {
        var wrapper = table.closest('.table-wrapper');
        var headers = Array.from(table.querySelectorAll('thead tr:last-child > th'));
        var rows = Array.from(table.querySelectorAll('tbody > tr'));
        // Only enhance ordinary rectangular product comparisons.
        if (!headers.length || !rows.length ||
            rows.some(function (row) { return row.children.length !== headers.length; })) return;
        var cards = document.createElement('div');
        cards.className = 'comparison-cards';
        cards.setAttribute('role', 'list');
        cards.setAttribute('aria-label', 'Productvergelijking');
        cards.hidden = true;
        rows.forEach(function (row, rowIndex) {
            var cells = Array.from(row.children);
            var card = document.createElement('article');
            card.className = 'comparison-card';
            card.setAttribute('role', 'listitem');
            var heading = document.createElement('h3');
            heading.id = 'comparison-card-' + index + '-' + rowIndex;
            copyContents(cells[0], heading);
            card.setAttribute('aria-labelledby', heading.id);
            card.appendChild(heading);
            var list = document.createElement('dl');
            card.appendChild(list);
            cells.slice(1).forEach(function (cell, cellIndex) {
                var label = headers[cellIndex + 1].textContent.trim();
                if (cell.querySelector('.button') || /^(actie|bekijk|link)/i.test(label)) {
                    var actions = document.createElement('div');
                    actions.className = 'comparison-card__actions';
                    copyContents(cell, actions);
                    card.appendChild(actions);
                } else {
                    var term = document.createElement('dt');
                    term.textContent = label;
                    var value = document.createElement('dd');
                    copyContents(cell, value);
                    list.appendChild(term);
                    list.appendChild(value);
                }
            });
            cards.appendChild(card);
        });
        wrapper.after(cards);
        comparisons.push({wrapper: wrapper, cards: cards});
    });

    function applyLayout() {
        helps.forEach(function (details) { details.open = !phone.matches; });
        comparisons.forEach(function (comparison) {
            // Exactly one representation participates in layout and accessibility.
            comparison.wrapper.hidden = phone.matches;
            comparison.cards.hidden = !phone.matches;
            var hint = comparison.wrapper.previousElementSibling;
            if (hint && hint.classList.contains('table-scroll-hint')) {
                hint.hidden = phone.matches ||
                    comparison.wrapper.scrollWidth <= comparison.wrapper.clientWidth + 1;
            }
        });
    }
    applyLayout();
    phone.addEventListener('change', applyLayout);

    // Opening a direct anchor inside a help panel must reveal its target.
    function revealHelpTarget() {
        if (!location.hash) return;
        var target;
        try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
        catch (error) { return; }
        if (!target) return;
        for (var parent = target.parentElement; parent; parent = parent.parentElement) {
            if (parent.matches('details.category-help')) parent.open = true;
        }
    }
    revealHelpTarget();
    window.addEventListener('hashchange', revealHelpTarget);
})();
