(function () {
    "use strict";

    function initCard(card) {
        var img = card.querySelector("[data-variant-image]");
        var swatches = card.querySelectorAll("[data-variant-swatch]");
        if (!img || !swatches.length) {
            return;
        }
        var affiliate = card.querySelector("[data-variant-affiliate]");
        var baseAlt = img.getAttribute("data-base-alt") || img.alt || "";

        function activate(swatch) {
            if (swatch.classList.contains("is-active")) {
                return;
            }

            var src = swatch.getAttribute("data-image");
            var url = swatch.getAttribute("data-affiliate");
            var name = swatch.getAttribute("data-name") || "";

            if (src && src !== img.getAttribute("src")) {
                var preload = new Image();
                img.style.opacity = "0";
                preload.onload = function () {
                    img.src = src;
                    img.alt = name ? baseAlt + " – " + name : baseAlt;
                    img.style.opacity = "1";
                };
                preload.onerror = function () {
                    img.style.opacity = "1";
                };
                preload.src = src;
            }

            if (url && affiliate) {
                affiliate.setAttribute("href", url);
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
