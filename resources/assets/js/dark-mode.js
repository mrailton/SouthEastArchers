/**
 * Shared dark mode Alpine.js component.
 * Reads preference from localStorage, falls back to system preference.
 * Toggles the `dark` class on <html> and persists the choice.
 */
export function registerDarkMode(Alpine) {
    Alpine.data('darkMode', () => ({
        dark: document.documentElement.classList.contains('dark'),

        toggle() {
            this.dark = !this.dark
            document.documentElement.classList.toggle('dark', this.dark)
            localStorage.setItem('theme', this.dark ? 'dark' : 'light')
        },
    }))
}

