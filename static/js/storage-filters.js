"use strict";

(function () {
    function init() {
        var filterBar = document.querySelector(".storage-filters-sticky");
        var sentinel = document.querySelector(".storage-filters-sentinel");

        if (!filterBar || !sentinel || !("IntersectionObserver" in window)) {
            return;
        }

        if (filterBar.dataset.stickyInitialized === "true") {
            return;
        }
        filterBar.dataset.stickyInitialized = "true";

        var observer = new IntersectionObserver(
            function (entries) {
                filterBar.classList.toggle("is-stuck", !entries[0].isIntersecting);
            },
            { threshold: 0 }
        );

        observer.observe(sentinel);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
