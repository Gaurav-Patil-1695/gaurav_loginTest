import React from 'react';
import { useTheme } from '../context/ThemeContext';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="theme-toggle"
    >
      {isDark ? (
        <span aria-hidden="true" className="theme-toggle__icon">
          &#9728;
        </span>
      ) : (
        <span aria-hidden="true" className="theme-toggle__icon">
          &#9790;
        </span>
      )}
    </button>
  );
}

export default ThemeToggle;
