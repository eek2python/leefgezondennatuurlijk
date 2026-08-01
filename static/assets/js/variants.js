(function () {
    "use strict";

    function initCard(card) {
        var img = card.querySelector("[data-variant-image]");
        var swatches = card.querySelectorAll("[data-variant-swatch]");
        if (!img || !swatches.length) {
            return;
        }
        var link = card.querySelector("[data-variant-affiliate]");
        var priceEl = card.querySelector("[data-variant-price]");
        var baseAlt = img.getAttribute("data-base-alt") || img.alt || "";
        var basePrice = priceEl ? priceEl.getAttribute("data-base-price") || "" : "";
        var defaultLabel = link ? link.textContent.trim() : "";
        var requestId = 0;

        function activate(swatch) {
            if (swatch.classList.contains("is-active")) {
                return;
            }

            var src = swatch.getAttribute("data-image");
            // Resolved linkgegevens per swatch komen uit Django (centrale
            // resolver, incl. gedocumenteerde familie-fallback naar de
            // productniveau-link). Geen eigen prioriteitslogica in JS en
            // nooit de URL van een andere swatch.
            var url = swatch.getAttribute("data-url") || "";
            var linkType = swatch.getAttribute("data-link-type") || "none";
            var rel = swatch.getAttribute("data-rel") || "";
            var label = swatch.getAttribute("data-label") || "";
            // Afgeleide niveaus zetten het attribuut altijd (ook leeg):
            // een aanwezige lege data-price wist het oude niveau expliciet
            // en valt nooit terug op productniveau. Alleen swatches zonder
            // attribuut (legacy handmatige niveaus) gebruiken de basis.
            var price = swatch.hasAttribute("data-price")
                ? (swatch.getAttribute("data-price") || "")
                : basePrice;
            var name = swatch.getAttribute("data-name") || "";

            if (src && src !== img.getAttribute("src")) {
                var current = ++requestId;
                var preload = new Image();
                img.style.opacity = "0";
                preload.onload = function () {
                    if (current !== requestId) {
                        return;
                    }
                    img.src = src;
                    img.alt = name ? baseAlt + " – " + name : baseAlt;
                    img.style.opacity = "1";
                };
                preload.onerror = function () {
                    if (current !== requestId) {
                        return;
                    }
                    img.style.opacity = "1";
                };
                preload.src = src;
            }

            // Expliciet zetten óf wissen: geen stale href/rel/label van een
            // vorige swatch laten staan.
            if (link) {
                if (url) {
                    link.setAttribute("href", url);
                    if (rel) {
                        link.setAttribute("rel", rel);
                    } else {
                        link.removeAttribute("rel");
                    }
                    link.setAttribute("data-link-type", linkType);
                    link.textContent = label || defaultLabel;
                    link.classList.toggle("primary", linkType !== "official");
                    link.hidden = false;
                } else {
                    link.removeAttribute("href");
                    link.removeAttribute("rel");
                    link.setAttribute("data-link-type", "none");
                    link.textContent = "";
                    link.classList.remove("primary");
                    link.hidden = true;
                }
            }

            if (priceEl) {
                priceEl.textContent = price || "";
                priceEl.hidden = !price;
            }

            for (var i = 0; i < swatches.length; i++) {
                var isActive = swatches[i] === swatch;
                swatches[i].classList.toggle("is-active", isActive);
                swatches[i].setAttribute("aria-pressed", isActive ? "true" : "false");
            }
        }

        for (var i = 0; i < swatches.length; i++) {
            (function (swatch) {
                swatch.addEventListener("click", function () {
                    activate(swatch);
                });
            })(swatches[i]);
        }
    }

    function init() {
        var cards = document.querySelectorAll("[data-variant-card]");
        for (var i = 0; i < cards.length; i++) {
            initCard(cards[i]);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
