"use strict";

(function () {
    function init() {
        var filterBar = document.querySelector(".storage-filters-sticky");
        var sentinel = document.querySelector(".storage-filters-sentinel");

        if (!filterBar || !sentinel) {
            return;
        }

        if (filterBar.dataset.stickyInitialized === "true") {
            return;
        }
        filterBar.dataset.stickyInitialized = "true";

        var mobile = window.matchMedia("(max-width: 1280px)");
        var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
        var naturalHeight = filterBar.offsetHeight;
        var updates = [];
        filterBar.querySelectorAll(".storage-filter-row").forEach(function (row, index) {
            var options = row.firstElementChild;
            options.id = options.id || "storage-filter-options-" + index;
            function arrow(label, glyph, direction) {
                var button = document.createElement("button");
                button.type = "button";
                button.className = "format-scroll-button";
                button.textContent = glyph;
                button.setAttribute("aria-label", label);
                button.setAttribute("aria-controls", options.id);
                button.hidden = true;
                button.addEventListener("click", function () {
                    options.scrollBy({
                        left: direction * Math.max(80, options.clientWidth * 0.75),
                        behavior: reducedMotion.matches ? "auto" : "smooth"
                    });
                });
                return button;
            }
            var previous = arrow("Vorige opties", "‹", -1);
            var next = arrow("Meer opties", "›", 1);
            row.insertBefore(previous, options);
            row.appendChild(next);
            function update(reveal) {
                var compact = mobile.matches && filterBar.classList.contains("is-stuck");
                var overflow = compact && options.scrollWidth > row.clientWidth + 1;
                previous.hidden = next.hidden = !overflow;
                if (compact && reveal) {
                    var selected = options.querySelector('[aria-current="page"]');
                    if (selected) {
                        var item = selected.getBoundingClientRect();
                        var container = options.getBoundingClientRect();
                        options.scrollLeft += item.left - container.left - (container.width - item.width) / 2;
                    }
                }
                previous.disabled = options.scrollLeft <= 1;
                next.disabled = options.scrollLeft + options.clientWidth >= options.scrollWidth - 1;
            }
            options.addEventListener("scroll", function () { update(false); }, {passive: true});
            updates.push(update);
        });
        var pending = false;
        function sync() {
            pending = false;
            // A direct jump can pass the sentinel without an intersection event.
            var stuck = sentinel.getBoundingClientRect().top <= 0;
            var changed = filterBar.classList.contains("is-stuck") !== stuck;
            if (!filterBar.classList.contains("is-stuck")) naturalHeight = filterBar.offsetHeight;
            // Keep the document's height stable when the mobile bar becomes fixed.
            sentinel.style.height = mobile.matches && stuck ? naturalHeight + "px" : "";
            filterBar.classList.toggle("is-stuck", stuck);
            updates.forEach(function (update) { update(changed); });
        }
        window.addEventListener("scroll", function () {
            if (!pending) {
                pending = true;
                requestAnimationFrame(sync);
            }
        }, {passive: true});
        window.addEventListener("resize", function () {
            sync();
            updates.forEach(function (update) { update(true); });
        });
        if ("ResizeObserver" in window) new ResizeObserver(sync).observe(filterBar);
        if (document.fonts) document.fonts.ready.then(sync);
        sync();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
