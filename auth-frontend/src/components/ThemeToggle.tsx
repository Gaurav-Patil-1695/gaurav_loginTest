import React from 'react';
import { useTheme } from '../context/ThemeContext';

const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();

  const isDark = theme === 'dark';
  const icon = isDark ? '☀' : '☾';
  const ariaLabel = isDark ? 'Switch to light mode' : 'Switch to dark mode';

  return (
    <button
      onClick={toggleTheme}
      aria-label={ariaLabel}
      style={{
        position: 'fixed',
        top: '1rem',
        right: '1rem',
        background: 'none',
        border: '2px solid currentColor',
        borderRadius: '50%',
        width: '2.5rem',
        height: '2.5rem',
        fontSize: '1.2rem',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        lineHeight: 1,
      }}
    >
      {icon}
    </button>
  );
};

export default ThemeToggle;
