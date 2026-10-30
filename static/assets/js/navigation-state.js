/* Read before the stylesheet so desktop navigation has the right first paint. */
(function() {
	'use strict';
	var root = document.documentElement;
	var keys = {
		sidebar: 'lng.navigation.desktop.sidebar',
		pannen: 'lng.navigation.desktop.pannen'
	};
	var values = { sidebar: true, pannen: false };

	Object.keys(keys).forEach(function(name) {
		try {
			var saved = localStorage.getItem(keys[name]);
			if (saved === 'true' || saved === 'false')
				values[name] = saved === 'true';
		} catch (error) {
			// Storage can be disabled; the current page must remain usable.
		}
		root.setAttribute('data-nav-' + name, String(values[name]));
	});

	window.navigationState = {
		get: function(name) { return values[name]; },
		set: function(name, open) {
			values[name] = open;
			root.setAttribute('data-nav-' + name, String(open));
			try {
				localStorage.setItem(keys[name], String(open));
			} catch (error) {
				// Keep the in-page state even if persistence is unavailable.
			}
		}
	};
})();
