import React from 'react';

function Branding(): JSX.Element {
  return (
    <div className="branding">
      <div className="branding__logo" aria-hidden="true">
        <svg
          width="48"
          height="48"
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label="App logo"
        >
          <rect
            width="48"
            height="48"
            rx="12"
            fill="var(--color-accent-primary)"
          />
          <path
            d="M24 12C18.477 12 14 16.477 14 22c0 3.536 1.822 6.648 4.572 8.488V36h10.856v-5.512C32.178 28.648 34 25.536 34 22c0-5.523-4.477-10-10-10z"
            fill="var(--color-surface)"
          />
        </svg>
      </div>
      <span className="branding__wordmark">AuthStarter</span>
    </div>
  );
}

export default Branding;
