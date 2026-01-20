const Theme = {
    // Initialize theme on page load
    init: () => {
        // Get saved theme or system preference
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

        Theme.apply(theme);

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('theme')) {
                Theme.apply(e.matches ? 'dark' : 'light');
            }
        });
    },

    // Apply theme to document
    apply: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);

        // Update toggle button if it exists
        const toggleBtn = document.getElementById('theme-toggle');
        if (toggleBtn) {
            toggleBtn.setAttribute('data-theme', theme);
        }
    },

    // Toggle between light and dark
    toggle: () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        Theme.apply(newTheme);
    },

    // Get current theme
    get: () => {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }
};

// Auto-initialize theme immediately (prevent flash)
Theme.init();
