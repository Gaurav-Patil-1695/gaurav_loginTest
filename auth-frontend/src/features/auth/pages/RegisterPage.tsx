import React, { useState, useId } from 'react';
import { register } from '../../../api/auth';

interface RegisterFormState {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

interface RegisterFormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  acceptTerms?: string;
  general?: string;
}

function getPasswordStrength(password: string): number {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  return score;
}

function validateForm(values: RegisterFormState): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!values.fullName || values.fullName.trim().length < 1) {
    errors.fullName = 'Full name is required.';
  } else if (values.fullName.length > 120) {
    errors.fullName = 'Full name is required.';
  }

  if (!values.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!values.password || values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(values.password)) {
    errors.password = 'Password must be at least 8 characters.';
  }

  if (!values.confirmPassword || values.confirmPassword !== values.password) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  if (!values.acceptTerms) {
    errors.acceptTerms = 'You must accept the Terms to continue.';
  }

  return errors;
}

const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
const strengthColors = [
  'transparent',
  'var(--color-error)',
  'var(--color-warning)',
  'var(--color-info)',
  'var(--color-success)',
];

export default function RegisterPage(): JSX.Element {
  const [values, setValues] = useState<RegisterFormState>({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });
  const [errors, setErrors] = useState<RegisterFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const idPrefix = useId();
  const fullNameId = `${idPrefix}-fullName`;
  const emailId = `${idPrefix}-email`;
  const passwordId = `${idPrefix}-password`;
  const confirmPasswordId = `${idPrefix}-confirmPassword`;
  const acceptTermsId = `${idPrefix}-acceptTerms`;

  const fullNameErrId = `${fullNameId}-err`;
  const emailErrId = `${emailId}-err`;
  const passwordErrId = `${passwordId}-err`;
  const confirmPasswordErrId = `${confirmPasswordId}-err`;
  const acceptTermsErrId = `${acceptTermsId}-err`;
  const generalErrId = `${idPrefix}-general-err`;

  const passwordStrength = getPasswordStrength(values.password);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const { name, value, type, checked } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setErrors({});
    setSuccessMessage(null);

    const validationErrors = validateForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        fullName: values.fullName,
        email: values.email,
        password: values.password,
        confirmPassword: values.confirmPassword,
        acceptTerms: values.acceptTerms,
      });
      setSuccessMessage('Account created! You can now sign in.');
    } catch (err: unknown) {
      if (
        err &&
        typeof err === 'object' &&
        'status' in err &&
        (err as { status: number }).status === 409
      ) {
        setErrors({ email: 'That email is already registered.' });
      } else {
        setErrors({ general: 'Something went wrong. Please try again.' });
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <style>{`
        :root {
          --color-accent-primary: #7c3aed;
          --color-accent-primary-hover: #6d28d9;
          --color-accent-primary-active: #5b21b6;
          --color-accent-disabled: #ddd6fe;
          --color-bg-app: #faf5ff;
          --color-border: #ede9fe;
          --color-border-strong: #c4b5fd;
          --color-border-default: #c4b5fd;
          --color-border-focus: #7c3aed;
          --color-border-error: #dc2626;
          --color-error: #DC2626;
          --color-error-light: #fef2f2;
          --color-error-border: #fecaca;
          --color-focus-ring: #a78bfa;
          --color-info: #2563EB;
          --color-link: #7c3aed;
          --color-text-link: #7c3aed;
          --color-text-link-hover: #6d28d9;
          --color-muted-surface: #f5f3ff;
          --color-bg-page: #faf5ff;
          --color-bg-card: #ffffff;
          --color-bg-input: #ffffff;
          --color-bg-input-disabled: #f5f3ff;
          --color-success: #16A34A;
          --color-success-light: #f0fdf4;
          --color-success-border: #bbf7d0;
          --color-surface: #ffffff;
          --color-text-muted: #a78bfa;
          --color-text-placeholder: #c4b5fd;
          --color-text-primary: #1e1b4b;
          --color-text-secondary: #4c1d95;
          --color-text-error: #dc2626;
          --color-text-success: #16a34a;
          --color-text-inverse: #ffffff;
          --color-warning: #D97706;
          --color-neutral-0: #ffffff;
          --color-neutral-400: #a78bfa;
          --elevation-1: 0 1px 2px rgba(109,40,217,0.06);
          --elevation-2: 0 4px 12px rgba(109,40,217,0.08);
          --elevation-card: 0 12px 32px rgba(109,40,217,0.12);
          --elevation-focus: 0 0 0 3px rgba(167,139,250,0.45);
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --family-mono: 'JetBrains Mono', 'Courier New', monospace;
          --radius-button: 8px;
          --radius-card: 16px;
          --radius-full: 9999px;
          --radius-input: 8px;
          --radius-lg: 12px;
          --radius-sm: 4px;
          --space-xs: 4px;
          --space-sm: 8px;
          --space-md: 16px;
          --space-lg: 24px;
          --space-xl: 32px;
          --space-2xl: 48px;
          --card-bg: #ffffff;
          --card-shadow: 0 12px 32px rgba(109,40,217,0.12);
          --card-radius: 16px;
          --card-width: 28rem;
          --card-padding: 2rem;
          --input-radius: 8px;
          --input-height: 2.5rem;
          --input-border-width: 1px;
          --input-font-size: 0.875rem;
          --input-padding-x: 0.75rem;
          --input-padding-y: 0.5rem;
          --button-radius: 8px;
          --button-height: 2.5rem;
          --button-font-size: 0.875rem;
          --button-font-weight: 600;
          --button-padding-x: 1rem;
          --button-padding-y: 0.5rem;
          --font-family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: var(--family-base);
          background-color: var(--color-bg-app);
          color: var(--color-text-primary);
          font-size: 16px;
          line-height: 1.5;
        }

        .auth-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-lg);
          background-color: var(--color-bg-app);
        }

        .auth-page__branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .auth-page__branding-title {
          font-size: 24px;
          font-weight: 700;
          color: var(--color-accent-primary);
          letter-spacing: -0.5px;
        }

        .auth-card {
          background: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-xl);
          width: 100%;
          max-width: 440px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin-bottom: var(--space-xs);
        }

        .auth-card__subtitle {
          font-size: 14px;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-xl);
          font-weight: 500;
          line-height: 1.5;
        }

        .auth-card__form {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }

        .auth-card__field {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .field__label {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-primary);
          line-height: 1.5;
        }

        .field__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .field__input {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          border: 1.5px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          font-size: 16px;
          font-family: var(--family-base);
          color: var(--color-text-primary);
          background: var(--color-surface);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
          line-height: 1.5;
        }

        .field__input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .field__input--error {
          border-color: var(--color-error);
        }

        .field__input--with-toggle {
          padding-right: 44px;
        }

        .field__toggle {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--space-xs);
          color: var(--color-text-muted);
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          justify-content: center;
          line-height: 1;
        }

        .field__toggle:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .field__error {
          font-size: 12px;
          color: var(--color-error);
          line-height: 1.5;
          display: flex;
          align-items: center;
          gap: var(--space-xs);
        }

        .field--error .field__input {
          border-color: var(--color-error);
        }

        .strength-meter {
          margin-top: var(--space-xs);
        }

        .strength-meter__bars {
          display: flex;
          gap: var(--space-xs);
          margin-bottom: var(--space-xs);
        }

        .strength-meter__bar {
          height: 4px;
          flex: 1;
          border-radius: var(--radius-full);
          background: var(--color-border);
          transition: background-color 0.2s;
        }

        .strength-meter__label {
          font-size: 12px;
          color: var(--color-text-muted);
          line-height: 1.5;
        }

        .auth-card__checkbox-field {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .checkbox-row {
          display: flex;
          align-items: flex-start;
          gap: var(--space-sm);
        }

        .checkbox-row__input {
          margin-top: 2px;
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
          flex-shrink: 0;
        }

        .checkbox-row__label {
          font-size: 14px;
          color: var(--color-text-secondary);
          line-height: 1.5;
          font-weight: 400;
          cursor: pointer;
        }

        .link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }

        .link:hover {
          text-decoration: underline;
        }

        .auth-card__submit {
          margin-top: var(--space-sm);
          padding: var(--space-sm) var(--space-md);
          background: var(--color-accent-primary);
          color: var(--color-text-inverse);
          border: none;
          border-radius: var(--radius-button);
          font-size: 16px;
          font-weight: 600;
          font-family: var(--family-base);
          cursor: pointer;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          transition: background-color 0.15s;
          min-height: 44px;
        }

        .auth-card__submit:hover:not(:disabled) {
          background: var(--color-accent-primary-hover);
        }

        .auth-card__submit:active:not(:disabled) {
          background: var(--color-accent-primary-active);
        }

        .auth-card__submit:disabled {
          background: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: var(--color-text-inverse);
          border-radius: var(--radius-full);
          animation: spin 0.7s linear infinite;
          flex-shrink: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card__footer {
          margin-top: var(--space-lg);
          text-align: center;
          font-size: 14px;
          color: var(--color-text-secondary);
          font-weight: 400;
        }

        .banner {
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          font-size: 14px;
          line-height: 1.5;
          font-weight: 500;
        }

        .banner--error {
          background: var(--color-error-light);
          color: var(--color-error);
          border: 1px solid var(--color-error-border);
        }

        .banner--success {
          background: var(--color-success-light);
          color: var(--color-success);
          border: 1px solid var(--color-success-border);
        }
      `}</style>

      <div className="auth-page__branding" aria-label="auth-starter">
        <span className="auth-page__branding-title">auth-starter</span>
      </div>

      <div className="auth-card" role="main">
        <h1 className="auth-card__title">Create account</h1>
        <p className="auth-card__subtitle">Sign up to get started today.</p>

        <div aria-live="polite" aria-atomic="true">
          {errors.general && (
            <div className="banner banner--error" role="alert" id={generalErrId}>
              {errors.general}
            </div>
          )}
          {successMessage && (
            <div className="banner banner--success" role="status">
              {successMessage}
            </div>
          )}
        </div>

        <form
          className="auth-card__form"
          onSubmit={handleSubmit}
          noValidate
          aria-busy={isSubmitting}
        >
          {/* Full Name */}
          <div className={`auth-card__field${errors.fullName ? ' field--error' : ''}`}>
            <label className="field__label" htmlFor={fullNameId}>
              Full name
            </label>
            <div className="field__input-wrapper">
              <input
                id={fullNameId}
                name="fullName"
                type="text"
                className={`field__input${errors.fullName ? ' field__input--error' : ''}`}
                value={values.fullName}
                onChange={handleChange}
                autoComplete="name"
                aria-describedby={errors.fullName ? fullNameErrId : undefined}
                aria-invalid={errors.fullName ? 'true' : 'false'}
                disabled={isSubmitting}
                maxLength={120}
              />
            </div>
            {errors.fullName && (
              <p className="field__error" id={fullNameErrId} role="alert">
                {errors.fullName}
              </p>
            )}
          </div>

          {/* Email */}
          <div className={`auth-card__field${errors.email ? ' field--error' : ''}`}>
            <label className="field__label" htmlFor={emailId}>
              Email address
            </label>
            <div className="field__input-wrapper">
              <input
                id={emailId}
                name="email"
                type="email"
                className={`field__input${errors.email ? ' field__input--error' : ''}`}
                value={values.email}
                onChange={handleChange}
                autoComplete="email"
                aria-describedby={errors.email ? emailErrId : undefined}
                aria-invalid={errors.email ? 'true' : 'false'}
                disabled={isSubmitting}
              />
            </div>
            {errors.email && (
              <p className="field__error" id={emailErrId} role="alert">
                {errors.email}
              </p>
            )}
          </div>

          {/* Password */}
          <div className={`auth-card__field${errors.password ? ' field--error' : ''}`}>
            <label className="field__label" htmlFor={passwordId}>
              Password
            </label>
            <div className="field__input-wrapper">
              <input
                id={passwordId}
                name="password"
                type={showPassword ? 'text' : 'password'}
                className={`field__input field__input--with-toggle${errors.password ? ' field__input--error' : ''}`}
                value={values.password}
                onChange={handleChange}
                autoComplete="new-password"
                aria-describedby={[
                  errors.password ? passwordErrId : '',
                  `${passwordId}-strength`,
                ]
                  .filter(Boolean)
                  .join(' ') || undefined}
                aria-invalid={errors.password ? 'true' : 'false'}
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="field__toggle"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={() => setShowPassword((v) => !v)}
                tabIndex={0}
              >
                {showPassword ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {errors.password && (
              <p className="field__error" id={passwordErrId} role="alert">
                {errors.password}
              </p>
            )}
            {values.password.length > 0 && (
              <div className="strength-meter" id={`${passwordId}-strength`} aria-label={`Password strength: ${strengthLabels[passwordStrength] || 'None'}`}>
                <div className="strength-meter__bars" aria-hidden="true">
                  {[1, 2, 3, 4].map((level) => (
                    <div
                      key={level}
                      className="strength-meter__bar"
                      style={{
                        background:
                          passwordStrength >= level
                            ? strengthColors[passwordStrength]
                            : 'var(--color-border)',
                      }}
                    />
                  ))}
                </div>
                <span className="strength-meter__label" aria-live="polite">
                  {strengthLabels[passwordStrength]
                    ? `Strength: ${strengthLabels[passwordStrength]}`
                    : ''}
                </span>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div className={`auth-card__field${errors.confirmPassword ? ' field--error' : ''}`}>
            <label className="field__label" htmlFor={confirmPasswordId}>
              Confirm password
            </label>
            <div className="field__input-wrapper">
              <input
                id={confirmPasswordId}
                name="confirmPassword"
                type={showConfirmPassword ? 'text' : 'password'}
                className={`field__input field__input--with-toggle${errors.confirmPassword ? ' field__input--error' : ''}`}
                value={values.confirmPassword}
                onChange={handleChange}
                autoComplete="new-password"
                aria-describedby={errors.confirmPassword ? confirmPasswordErrId : undefined}
                aria-invalid={errors.confirmPassword ? 'true' : 'false'}
                disabled={isSubmitting}
              />
              <button
                type="button"
                className="field__toggle"
                aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                onClick={() => setShowConfirmPassword((v) => !v)}
                tabIndex={0}
              >
                {showConfirmPassword ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="field__error" id={confirmPasswordErrId} role="alert">
                {errors.confirmPassword}
              </p>
            )}
          </div>

          {/* Accept Terms */}
          <div className="auth-card__checkbox-field">
            <div className="checkbox-row">
              <input
                id={acceptTermsId}
                name="acceptTerms"
                type="checkbox"
                className="checkbox-row__input"
                checked={values.acceptTerms}
                onChange={handleChange}
                aria-describedby={errors.acceptTerms ? acceptTermsErrId : undefined}
                aria-invalid={errors.acceptTerms ? 'true' : 'false'}
                disabled={isSubmitting}
              />
              <label className="checkbox-row__label" htmlFor={acceptTermsId}>
                I agree to the{' '}
                <a className="link" href="/terms" target="_blank" rel="noopener noreferrer">
                  Terms of Service
                </a>{' '}
                and{' '}
                <a className="link" href="/privacy" target="_blank" rel="noopener noreferrer">
                  Privacy Policy
                </a>.
              </label>
            </div>
            {errors.acceptTerms && (
              <p className="field__error" id={acceptTermsErrId} role="alert">
                {errors.acceptTerms}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="auth-card__submit"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className="spinner" aria-hidden="true" />}
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-card__footer">
          Already have an account?{' '}
          <a className="link" href="/login">
            Sign in
          </a>
        </p>
      </div>
    </div>
  );
}
