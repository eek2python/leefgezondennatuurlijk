(function () {
    "use strict";

    function initCard(card) {
        var buttons = card.querySelectorAll("[data-shape-option]");
        if (buttons.length < 2) {
            return;
        }
        var scope = card.hasAttribute("data-shape-page") ? document : card;
        var img = scope.querySelector("[data-shape-image]");
        var summary = scope.querySelector("[data-shape-summary]");
        var link = scope.querySelector("[data-shape-affiliate]");
        var disabledEl = scope.querySelector("[data-shape-affiliate-disabled]");
        var capacityEl = scope.querySelector("[data-shape-capacity]");
        var totalCapacityEl = scope.querySelector("[data-shape-total-capacity]");
        var requestId = 0;

        function activate(button) {
            if (button.getAttribute("aria-pressed") === "true") {
                return;
            }

            var src = button.getAttribute("data-image") || "";
            var alt = button.getAttribute("data-alt") || "";
            var url = button.getAttribute("data-affiliate") || "";
            var label = button.getAttribute("data-label") || "";
            var summaryText = button.getAttribute("data-summary") || "";

            if (img && src && src !== img.getAttribute("src")) {
                var current = ++requestId;
                var preload = new Image();
                img.style.opacity = "0";
                preload.onload = function () {
                    if (current !== requestId) {
                        return;
                    }
                    img.src = src;
                    if (alt) {
                        img.alt = alt;
                    }
                    img.style.opacity = "1";
                };
                preload.onerror = function () {
                    if (current !== requestId) {
                        return;
                    }
                    img.style.opacity = "1";
                };
                preload.src = src;
            } else if (img && alt && src) {
                img.alt = alt;
            }

            if (summary && summaryText) {
                summary.textContent = summaryText;
            }

            if (capacityEl) {
                var capacity = button.getAttribute("data-capacity") || "";
                if (capacity) {
                    capacityEl.textContent = capacity;
                }
            }
            if (totalCapacityEl) {
                var totalCapacity = button.getAttribute("data-total-capacity") || "";
                if (totalCapacity) {
                    totalCapacityEl.textContent = totalCapacity;
                }
            }

            if (link) {
                if (url) {
                    link.setAttribute("href", url);
                    link.setAttribute(
                        "aria-label",
                        "Bekijk prijs en reviews – " + label
                    );
                    link.hidden = false;
                    if (disabledEl) {
                        disabledEl.hidden = true;
                    }
                } else {
                    link.hidden = true;
                    if (disabledEl) {
                        disabledEl.hidden = false;
                    }
                }
            }

            for (var i = 0; i < buttons.length; i++) {
                var isActive = buttons[i] === button;
                buttons[i].classList.toggle("is-active", isActive);
                buttons[i].setAttribute(
                    "aria-pressed",
                    isActive ? "true" : "false"
                );
            }

            if (typeof window.gtag === "function") {
                window.gtag("event", "select_product_variant", {
                    product_slug: card.getAttribute("data-product-slug") || "",
                    product_name: card.getAttribute("data-product-name") || "",
                    variant_id: button.getAttribute("data-variant-id") || "",
                    variant_label: label,
                    shape: button.getAttribute("data-shape") || "",
                    capacity: button.getAttribute("data-capacity") || "",
                    category: window.location.pathname
                });
            }
        }

        for (var i = 0; i < buttons.length; i++) {
            (function (button) {
                button.addEventListener("click", function () {
                    activate(button);
                });
            })(buttons[i]);
        }
    }

    function init() {
        var cards = document.querySelectorAll("[data-shape-card]");
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
