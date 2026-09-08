import React from 'react';

interface SubmitButtonProps {
  label: string;
  isSubmitting: boolean;
  disabled?: boolean;
}

function SubmitButton({
  label,
  isSubmitting,
  disabled = false,
}: SubmitButtonProps): React.JSX.Element {
  const isDisabled = disabled || isSubmitting;

  return (
    <button
      type="submit"
      className={`submit-button${isSubmitting ? ' submit-button--loading' : ''}`}
      disabled={isDisabled}
      aria-busy={isSubmitting ? 'true' : 'false'}
    >
      {isSubmitting && (
        <svg
          className="submit-button__spinner"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
          focusable="false"
        >
          <circle
            cx="9"
            cy="9"
            r="7"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="32"
            strokeDashoffset="12"
          />
        </svg>
      )}
      <span className="submit-button__label">{label}</span>
    </button>
  );
}

export default SubmitButton;
