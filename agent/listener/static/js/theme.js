/*
 * Color theme handling (light / dark / auto).
 * Loaded synchronously in <head> so the theme is applied before first paint.
 * The choice is stored per browser in localStorage; "auto" follows the OS setting.
 */
(function() {
    var STORAGE_KEY = 'ncpa-theme';
    var MODES = ['auto', 'light', 'dark'];
    var LABELS = { auto: 'Auto (system)', light: 'Light', dark: 'Dark' };
    var ICONS = { auto: 'fa-circle-half-stroke', light: 'fa-sun', dark: 'fa-moon' };
    var media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    function getMode() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved === 'light' || saved === 'dark') {
                return saved;
            }
        } catch (e) {}
        return 'auto';
    }

    function setMode(mode) {
        try {
            if (mode === 'auto') {
                localStorage.removeItem(STORAGE_KEY);
            } else {
                localStorage.setItem(STORAGE_KEY, mode);
            }
        } catch (e) {}
        apply();
    }

    function resolve(mode) {
        if (mode === 'auto') {
            return media && media.matches ? 'dark' : 'light';
        }
        return mode;
    }

    function updateToggle(mode) {
        var btn = document.getElementById('theme-toggle');
        if (!btn) {
            return;
        }
        var icon = btn.querySelector('i');
        if (icon) {
            icon.className = 'fa ' + ICONS[mode] + ' fa-14 fa-l';
        }
        var label = btn.querySelector('.theme-toggle-label');
        if (label) {
            label.textContent = LABELS[mode];
        }
        var title = 'Theme: ' + LABELS[mode] + ' - click to change';
        btn.setAttribute('title', title);
        btn.setAttribute('aria-label', title);
    }

    function apply() {
        var mode = getMode();
        document.documentElement.setAttribute('data-bs-theme', resolve(mode));
        updateToggle(mode);
    }

    apply();

    if (media) {
        var onSystemChange = function() {
            if (getMode() === 'auto') {
                apply();
            }
        };
        if (media.addEventListener) {
            media.addEventListener('change', onSystemChange);
        } else if (media.addListener) {
            media.addListener(onSystemChange);
        }
    }

    // Keep other open tabs in sync when the choice changes
    window.addEventListener('storage', function(e) {
        if (e.key === STORAGE_KEY) {
            apply();
        }
    });
    
    document.addEventListener('DOMContentLoaded', function() {
        var btn = document.getElementById('theme-toggle');
        if (!btn) {
            return;
        }
        updateToggle(getMode());
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            var next = MODES[(MODES.indexOf(getMode()) + 1) % MODES.length];
            setMode(next);
        });
    });
})();