/* Reuse server-rendered content; normal URLs and tables remain the no-JS fallback. */
(function () {
    'use strict';
    var phone = window.matchMedia('(max-width: 736px)');
    var helps = Array.from(document.querySelectorAll('details.category-help'));
    var comparisons = [];

    function text(element) {
        return element.textContent.replace(/\s+/g, ' ').trim();
    }

    document.querySelectorAll('.table-wrapper table.product-table').forEach(function (table, index) {
        var wrapper = table.closest('.table-wrapper');
        var headers = Array.from(table.querySelectorAll('thead tr:last-child > th'));
        var rows = Array.from(table.querySelectorAll('tbody > tr'));
        if (!headers.length || !rows.length ||
            rows.some(function (row) { return row.children.length !== headers.length; })) return;
        var columns = [];
        function addColumn(pattern, label, width, extract, requireDifference) {
            var columnIndex = headers.findIndex(function (header) { return pattern.test(text(header)); });
            if (columnIndex < 0) return;
            var values = rows.map(function (row) { return extract(row.children[columnIndex]); });
            if (!values.some(function (value) { return value && value !== '—'; })) return;
            if (requireDifference &&
                (new Set(values).size < 2 || values.some(function (value) { return value.length > 64; }))) return;
            columns.push({label: label, width: width, values: values});
        }
        // Keep the first viewport useful: names, editorial score and price first.
        addColumn(/beoordeling/i, 'Oordeel', 72, function (cell) {
            var value = cell.querySelector('.rating-value');
            return value ? text(value) : text(cell).replace(/^Onze beoordeling:\s*/i, '');
        }, false);
        addColumn(/prijs/i, 'Prijs', 64, text, false);
        var coreCount = columns.length;
        addColumn(/^inhoud$/i, 'Inhoud', 104, text, true);
        addColumn(/^totale inhoud$/i, 'Totale inhoud', 104, text, true);
        addColumn(/^pannetjes$/i, 'Pannetjes', 88, text, true);
        if (columns.length < coreCount + 2) addColumn(/^vermogen$/i, 'Vermogen', 96, text, true);
        if (columns.length === coreCount) addColumn(/^formaat$/i, 'Formaat', 104, text, true);
        if (columns.length < coreCount + 2) {
            // The first feature comes from the existing features-only cell.
            // Omit the column altogether if any value needs a long description.
            addColumn(/eigenschappen|kenmerken/i, 'Kenmerken', 144, function (cell) {
                return text(cell).split('·')[0].trim();
            }, true);
        }
        if (table.dataset.comparisonCategory === 'gourmetsets') {
            // These details matter even when all sets share the same PFAS status.
            // Read the source cells verbatim, including unknown/not-applicable values.
            addColumn(/^type plaat$/i, 'Type plaat', 180, text, false);
            addColumn(/^temperatuurregeling$/i, 'Temperatuurregeling', 160, text, false);
            addColumn(/^PFAS-vrij: bakplaat$/i, 'PFAS-vrij: bakplaat', 112, text, false);
            addColumn(/^PFAS-vrij: pannetjes$/i, 'PFAS-vrij: pannetjes', 112, text, false);
        }

        var hint = document.createElement('p');
        hint.className = 'compact-comparison-hint';
        hint.id = 'compact-comparison-hint-' + index;
        hint.textContent = 'Veeg opzij om de overige vergelijkingspunten te bekijken';
        hint.hidden = true;
        var scroll = document.createElement('div');
        scroll.className = 'compact-comparison-scroll';
        scroll.tabIndex = 0;
        scroll.setAttribute('role', 'region');
        scroll.setAttribute('aria-label', 'Compacte productvergelijking');
        scroll.hidden = true;
        var compact = document.createElement('table');
        compact.className = 'compact-comparison-table';
        compact.style.setProperty('--comparison-min-width',
            (140 + columns.reduce(function (sum, column) { return sum + column.width; }, 0)) + 'px');
        var caption = compact.createCaption();
        caption.textContent = 'Redactionele vergelijking van ' + rows.length + ' producten';
        var colgroup = document.createElement('colgroup');
        [140].concat(columns.map(function (column) { return column.width; })).forEach(function (width) {
            var col = document.createElement('col');
            col.style.width = width + 'px';
            colgroup.appendChild(col);
        });
        compact.appendChild(colgroup);
        var headerRow = compact.createTHead().insertRow();
        ['Product'].concat(columns.map(function (column) { return column.label; })).forEach(function (label) {
            var header = document.createElement('th');
            header.scope = 'col';
            header.textContent = label;
            headerRow.appendChild(header);
        });
        var body = compact.createTBody();
        var productCards = Array.from(document.querySelectorAll('#main .product-block'));
        rows.forEach(function (row, rowIndex) {
            var sourceName = row.children[0].cloneNode(true);
            sourceName.querySelectorAll('.product-badge').forEach(function (badge) { badge.remove(); });
            var name = text(sourceName);
            var productCell = document.createElement('th');
            productCell.scope = 'row';
            var slugLink = row.querySelector('[data-product-slug]');
            var slug = slugLink && slugLink.getAttribute('data-product-slug');
            var card = productCards.find(function (candidate) {
                var link = candidate.querySelector('h3 a');
                if (!link) return false;
                if (slug && link.getAttribute('href') === '/product/' + slug + '/') return true;
                return text(link).replace(/^\d+\.\s*/, '').indexOf(name) === 0;
            });
            var headingLink = card && card.querySelector('h3 a');
            if (headingLink) {
                var nameLink = document.createElement('a');
                nameLink.className = 'compact-comparison-product';
                nameLink.href = headingLink.getAttribute('href');
                nameLink.textContent = name;
                nameLink.setAttribute('aria-label', name + ': ga naar productkaart');
                nameLink.addEventListener('click', function (event) {
                    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
                    event.preventDefault();
                    var filterHeight = parseFloat(getComputedStyle(document.documentElement)
                        .getPropertyValue('--sticky-filter-height')) || 0;
                    window.scrollTo({
                        top: card.getBoundingClientRect().top + window.scrollY - Math.max(56, filterHeight) - 16,
                        behavior: 'auto'
                    });
                    headingLink.focus({preventScroll: true});
                });
                productCell.appendChild(nameLink);
            } else {
                productCell.appendChild(document.createTextNode(name));
            }
            row.children[0].querySelectorAll('.product-badge').forEach(function (badge) {
                productCell.appendChild(document.createTextNode(' '));
                productCell.appendChild(badge.cloneNode(true));
            });
            var compactRow = body.insertRow();
            compactRow.appendChild(productCell);
            columns.forEach(function (column) {
                compactRow.insertCell().textContent = column.values[rowIndex] || '—';
            });
        });
        scroll.appendChild(compact);
        wrapper.after(hint, scroll);
        function updateHint() {
            var overflow = phone.matches && columns.length > 0 && scroll.scrollWidth > scroll.clientWidth + 1;
            hint.hidden = !overflow;
            if (overflow) scroll.setAttribute('aria-describedby', hint.id);
            else scroll.removeAttribute('aria-describedby');
        }
        scroll.addEventListener('keydown', function (event) {
            if (event.target !== scroll || (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft')) return;
            if (scroll.scrollWidth <= scroll.clientWidth) return;
            event.preventDefault();
            scroll.scrollLeft += event.key === 'ArrowRight' ? 80 : -80;
        });
        if ('ResizeObserver' in window) new ResizeObserver(updateHint).observe(scroll);
        comparisons.push({wrapper: wrapper, scroll: scroll, hint: hint, hasData: columns.length > 0, update: updateHint});
    });

    function applyLayout() {
        helps.forEach(function (details) { details.open = !phone.matches; });
        comparisons.forEach(function (comparison) {
            // Exactly one representation participates in layout and accessibility.
            comparison.wrapper.hidden = phone.matches;
            comparison.scroll.hidden = !phone.matches || !comparison.hasData;
            comparison.update();
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
