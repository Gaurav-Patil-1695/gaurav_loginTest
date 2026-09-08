import React from 'react';

interface Rule {
  key: string;
  label: string;
  test: (password: string) => boolean;
}

const RULES: Rule[] = [
  {
    key: 'length',
    label: 'At least 8 characters',
    test: (p) => p.length >= 8,
  },
  {
    key: 'uppercase',
    label: 'One uppercase letter',
    test: (p) => /[A-Z]/.test(p),
  },
  {
    key: 'lowercase',
    label: 'One lowercase letter',
    test: (p) => /[a-z]/.test(p),
  },
  {
    key: 'number',
    label: 'One number',
    test: (p) => /[0-9]/.test(p),
  },
];

interface PasswordStrengthMeterProps {
  password: string;
}

function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps): JSX.Element {
  const results = RULES.map((rule) => ({
    ...rule,
    passed: rule.test(password),
  }));

  const passedCount = results.filter((r) => r.passed).length;

  return (
    <div className="password-strength" aria-label="Password strength checklist">
      <ul className="password-strength__checklist" role="list">
        {results.map((rule) => (
          <li
            key={rule.key}
            className={`password-strength__rule${
              rule.passed ? ' password-strength__rule--passed' : ' password-strength__rule--failed'
            }`}
            aria-label={`${rule.label}: ${rule.passed ? 'met' : 'not met'}`}
          >
            <span
              className="password-strength__rule-icon"
              aria-hidden="true"
            >
              {rule.passed ? (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  focusable="false"
                >
                  <circle cx="7" cy="7" r="7" fill="var(--color-success)" />
                  <path
                    d="M4 7l2 2 4-4"
                    stroke="var(--color-surface)"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  focusable="false"
                >
                  <circle cx="7" cy="7" r="7" fill="var(--color-border)" />
                </svg>
              )}
            </span>
            <span className="password-strength__rule-label">{rule.label}</span>
          </li>
        ))}
      </ul>
      <div
        className="password-strength__bar"
        role="meter"
        aria-label="Password strength"
        aria-valuenow={passedCount}
        aria-valuemin={0}
        aria-valuemax={RULES.length}
      >
        {RULES.map((rule, index) => (
          <div
            key={rule.key}
            className={`password-strength__bar-segment${
              index < passedCount
                ? ' password-strength__bar-segment--filled'
                : ''
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export default PasswordStrengthMeter;
