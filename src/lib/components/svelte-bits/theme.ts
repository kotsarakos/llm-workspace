import { readable } from 'svelte/store';

/** True while the app is in dark mode (tracks the `dark` class on <html>). */
export const isDarkMode = readable(true, (set) => {
	if (typeof document === 'undefined') return;
	const root = document.documentElement;
	const sync = () => set(root.classList.contains('dark'));
	sync();
	const observer = new MutationObserver(sync);
	observer.observe(root, { attributes: true, attributeFilter: ['class'] });
	return () => observer.disconnect();
});

/** Shared llm-workspace accent palette. */
export const ACCENT = {
	blue: '#3b82f6',
	violet: '#8b5cf6',
	cyan: '#06b6d4'
};
export const ACCENT_STOPS = [ACCENT.blue, ACCENT.violet, ACCENT.cyan];
