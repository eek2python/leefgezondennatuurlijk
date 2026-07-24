(function () {
    "use strict";

    function readVariantData(card) {
        var script = card.querySelector('script[id^="variant-data-"]');
        if (!script) {
            return null;
        }
        try {
            return JSON.parse(script.textContent);
        } catch (err) {
            return null;
        }
    }

    function getMatchingVariants(variants, selections) {
        return variants.filter(function (variant) {
            return Object.keys(selections).every(function (key) {
                return variant.options[key] === selections[key];
            });
        });
    }

    function getExactVariant(variants, selections) {
        var matches = getMatchingVariants(variants, selections);
        return matches.length ? matches[0] : null;
    }

    function selectFallbackVariant(variants, changedSelector, selections) {
        var candidates = variants.filter(function (variant) {
            return variant.options[changedSelector] === selections[changedSelector];
        });
        if (!candidates.length) {
            return null;
        }
        var otherKeys = Object.keys(selections).filter(function (key) {
            return key !== changedSelector;
        });
        var best = null;
        var bestScore = -1;
        for (var i = 0; i < candidates.length; i++) {
            var score = 0;
            for (var j = 0; j < otherKeys.length; j++) {
                if (candidates[i].options[otherKeys[j]] === selections[otherKeys[j]]) {
                    score++;
                }
            }
            if (candidates[i].is_default) {
                score += 0.5;
            }
            if (score > bestScore) {
                bestScore = score;
                best = candidates[i];
            }
        }
        return best;
    }

    function updateAvailableOptions(card, variants, selections) {
        var buttons = card.querySelectorAll("[data-variant-option]");
        for (var i = 0; i < buttons.length; i++) {
            var button = buttons[i];
            var key = button.getAttribute("data-selector-key");
            var rawValue = button.getAttribute("data-option-value");
            var value = coerceValue(variants, key, rawValue);
            var available = variants.some(function (variant) {
                if (variant.options[key] !== value) {
                    return false;
                }
                return Object.keys(selections).every(function (k) {
                    return k === key || variant.options[k] === selections[k];
                });
            });
            var isActive = selections[key] === value;
            button.classList.toggle("is-active", isActive);
            button.classList.toggle("product-variant-option--active", isActive);
            button.classList.toggle(
                "product-variant-option--unavailable",
                !available
            );
            button.setAttribute("aria-pressed", isActive ? "true" : "false");
            if (available) {
                button.removeAttribute("disabled");
                button.removeAttribute("aria-disabled");
            } else {
                button.setAttribute("disabled", "");
                button.setAttribute("aria-disabled", "true");
            }
        }
    }

    function coerceValue(variants, key, rawValue) {
        for (var i = 0; i < variants.length; i++) {
            var value = variants[i].options[key];
            if (String(value) === rawValue) {
                return value;
            }
        }
        return rawValue;
    }

    function renderVariant(card, variant, refs) {
        if (refs.img && variant.image && variant.image !== refs.img.getAttribute("src")) {
            var current = ++refs.requestId.value;
            var preload = new Image();
            refs.img.style.opacity = "0";
            preload.onload = function () {
                if (current !== refs.requestId.value) {
                    return;
                }
                refs.img.src = variant.image;
                if (variant.alt) {
                    refs.img.alt = variant.alt;
                }
                refs.img.style.opacity = "1";
            };
            preload.onerror = function () {
                if (current !== refs.requestId.value) {
                    return;
                }
                refs.img.style.opacity = "1";
            };
            preload.src = variant.image;
        } else if (refs.img && variant.alt && variant.image) {
            refs.img.alt = variant.alt;
        }

        if (refs.summary && variant.summary) {
            refs.summary.textContent = variant.summary;
        }
        if (refs.capacityEl && variant.capacity) {
            refs.capacityEl.textContent = variant.capacity;
        }
        if (refs.totalCapacityEl && variant.total_capacity) {
            refs.totalCapacityEl.textContent = variant.total_capacity;
        }

        if (refs.link) {
            if (variant.affiliate_url) {
                refs.link.setAttribute("href", variant.affiliate_url);
                refs.link.setAttribute(
                    "aria-label",
                    "Bekijk prijs en reviews – " + variant.label
                );
                refs.link.hidden = false;
                if (refs.disabledEl) {
                    refs.disabledEl.hidden = true;
                }
            } else {
                refs.link.hidden = true;
                if (refs.disabledEl) {
                    refs.disabledEl.hidden = false;
                }
            }
        }
    }

    function initializeProductVariantCard(card) {
        var data = readVariantData(card);
        if (!data || !data.variants || !data.variants.length) {
            return;
        }
        var buttons = card.querySelectorAll("[data-variant-option]");
        if (!buttons.length) {
            return;
        }
        var scope = card.hasAttribute("data-shape-page") ? document : card;
        var refs = {
            img: scope.querySelector("[data-shape-image]"),
            summary: scope.querySelector("[data-shape-summary]"),
            link: scope.querySelector("[data-shape-affiliate]"),
            disabledEl: scope.querySelector("[data-shape-affiliate-disabled]"),
            capacityEl: scope.querySelector("[data-shape-capacity]"),
            totalCapacityEl: scope.querySelector("[data-shape-total-capacity]"),
            requestId: { value: 0 }
        };

        var variants = data.variants;
        var defaultVariant = null;
        for (var i = 0; i < variants.length; i++) {
            if (variants[i].id === data.default_id) {
                defaultVariant = variants[i];
            }
        }
        if (!defaultVariant) {
            defaultVariant = variants[0];
        }
        var selections = {};
        Object.keys(defaultVariant.options).forEach(function (key) {
            selections[key] = defaultVariant.options[key];
        });

        function handleSelect(button) {
            if (button.hasAttribute("disabled")) {
                return;
            }
            var key = button.getAttribute("data-selector-key");
            var value = coerceValue(
                variants,
                key,
                button.getAttribute("data-option-value")
            );
            if (selections[key] === value) {
                return;
            }
            selections[key] = value;
            var variant = getExactVariant(variants, selections);
            if (!variant) {
                variant = selectFallbackVariant(variants, key, selections);
            }
            if (!variant) {
                return;
            }
            Object.keys(variant.options).forEach(function (k) {
                selections[k] = variant.options[k];
            });
            updateAvailableOptions(card, variants, selections);
            renderVariant(card, variant, refs);

            if (typeof window.gtag === "function") {
                window.gtag("event", "select_product_variant", {
                    product_slug: card.getAttribute("data-product-slug") || "",
                    product_name: card.getAttribute("data-product-name") || "",
                    variant_id: variant.id,
                    variant_label: variant.label,
                    changed_selector: key,
                    capacity: variant.capacity || "",
                    category: window.location.pathname
                });
            }
        }

        for (var b = 0; b < buttons.length; b++) {
            (function (button) {
                button.addEventListener("click", function () {
                    handleSelect(button);
                });
            })(buttons[b]);
        }
    }

    function init() {
        var cards = document.querySelectorAll("[data-shape-card]");
        for (var i = 0; i < cards.length; i++) {
            initializeProductVariantCard(cards[i]);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
