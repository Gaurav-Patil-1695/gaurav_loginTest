import React, { useState, useId } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../../api/auth';

interface LoginFormState {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface LoginFormErrors {
  email?: string;
  password?: string;
  form?: string;
}

function validateLoginForm(values: LoginFormState): LoginFormErrors {
  const errors: LoginFormErrors = {};

  if (!values.email) {
    errors.email = 'Enter a valid email address.';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!values.password || values.password.length < 1) {
    errors.password = 'Password is required.';
  }

  return errors;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const emailId = useId();
  const passwordId = useId();
  const rememberMeId = useId();
  const emailErrorId = useId();
  const passwordErrorId = useId();
  const formErrorId = useId();

  const [values, setValues] = useState<LoginFormState>({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, email: e.target.value }));
    if (errors.email) {
      setErrors((prev) => ({ ...prev, email: undefined }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, password: e.target.value }));
    if (errors.password) {
      setErrors((prev) => ({ ...prev, password: undefined }));
    }
  };

  const handleRememberMeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, rememberMe: e.target.checked }));
  };

  const handleTogglePassword = () => {
    setShowPassword((prev) => !prev);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const validationErrors = validateLoginForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    try {
      await login({
        email: values.email,
        password: values.password,
        rememberMe: values.rememberMe,
      });
      navigate('/');
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Invalid email or password.';
      setErrors({ form: message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-root">
      <style>{`
        :root {
          --color-accent-disabled: #c4b5fd;
          --color-accent-primary: #7c3aed;
          --color-accent-primary-active: #5b21b6;
          --color-accent-primary-hover: #6d28d9;
          --color-bg-app: #f5f3ff;
          --color-border: #ede9fe;
          --color-border-strong: #ddd6fe;
          --color-error: #DC2626;
          --color-error-light: var(--color-error-light, #fef2f2);
          --color-error-border: var(--color-error-border, #fca5a5);
          --color-focus-ring: #a78bfa;
          --color-info: #2563EB;
          --color-link: #7c3aed;
          --color-muted-surface: #faf5ff;
          --color-success: #16A34A;
          --color-surface: #ffffff;
          --color-text-muted: #a78bfa;
          --color-text-primary: #1e1b4b;
          --color-text-secondary: #4c1d95;
          --color-warning: #D97706;

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

          --space-2xl: 48px;
          --space-lg: 24px;
          --space-md: 16px;
          --space-sm: 8px;
          --space-xl: 32px;
          --space-xs: 4px;
        }

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        .auth-root {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-family: var(--family-base);
          color: var(--color-text-primary);
          padding: var(--space-md);
        }

        .auth-branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .auth-branding__logo {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          background-color: var(--color-accent-primary);
          border-radius: var(--radius-lg);
          margin-bottom: var(--space-sm);
        }

        .auth-branding__logo svg {
          width: 28px;
          height: 28px;
          fill: var(--color-surface);
        }

        .auth-branding__name {
          font-size: 18px;
          font-weight: 600;
          line-height: 1.25;
          color: var(--color-text-primary);
        }

        .auth-card {
          background-color: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-xl);
          width: 100%;
          max-width: 420px;
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
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-lg);
        }

        .auth-card__body {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }

        .auth-card__field {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .auth-card__field label {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-primary);
        }

        .auth-card__field .field__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .auth-card__field input[type='email'],
        .auth-card__field input[type='password'],
        .auth-card__field input[type='text'] {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-size: 16px;
          font-family: var(--family-base);
          line-height: 1.5;
          color: var(--color-text-primary);
          background-color: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          outline: none;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }

        .auth-card__field input[type='password'],
        .auth-card__field input[type='text'] {
          padding-right: 44px;
        }

        .auth-card__field input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .auth-card__field input.field--error {
          border-color: var(--color-error);
        }

        .auth-card__field input.field--error:focus {
          box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
        }

        .field__toggle-btn {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--space-xs);
          color: var(--color-text-secondary);
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          justify-content: center;
          line-height: 1;
        }

        .field__toggle-btn:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 1px;
        }

        .field__toggle-btn svg {
          width: 20px;
          height: 20px;
        }

        .field__error {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
        }

        .auth-card__row {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .auth-card__checkbox-label {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          font-size: 14px;
          font-weight: 400;
          color: var(--color-text-secondary);
          cursor: pointer;
          user-select: none;
        }

        .auth-card__checkbox-label input[type='checkbox'] {
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
        }

        .auth-card__link {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-link);
          text-decoration: none;
        }

        .auth-card__link:hover {
          text-decoration: underline;
        }

        .auth-card__link:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
          border-radius: var(--radius-sm);
        }

        .btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-xs);
          font-size: 16px;
          font-weight: 600;
          font-family: var(--family-base);
          line-height: 1.5;
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-button);
          border: none;
          cursor: pointer;
          width: 100%;
          transition: background-color 0.15s ease;
          margin-top: var(--space-xs);
        }

        .btn--primary {
          background-color: var(--color-accent-primary);
          color: var(--color-surface);
        }

        .btn--primary:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .btn--primary:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .btn--primary:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .btn--primary:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .btn__spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: var(--color-surface);
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
        }

        .form-error-banner {
          background-color: var(--color-error-light, #fef2f2);
          border: 1px solid var(--color-error-border, #fca5a5);
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          color: var(--color-error);
          font-size: 14px;
          line-height: 1.5;
        }
      `}</style>

      <div className="auth-branding" aria-hidden="false">
        <div className="auth-branding__logo" aria-hidden="true">
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z" />
          </svg>
        </div>
        <div className="auth-branding__name">auth-starter</div>
      </div>

      <form
        className="auth-card"
        aria-labelledby="login-title"
        onSubmit={handleSubmit}
        noValidate
      >
        <h1 className="auth-card__title" id="login-title">
          Sign in
        </h1>
        <p className="auth-card__subtitle">Welcome back. Enter your credentials to continue.</p>

        <div className="auth-card__body">
          {errors.form && (
            <div
              className="form-error-banner"
              role="alert"
              aria-live="polite"
              id={formErrorId}
            >
              {errors.form}
            </div>
          )}

          <div className="auth-card__field">
            <label htmlFor={emailId}>Email address</label>
            <div className="field__input-wrapper">
              <input
                id={emailId}
                type="email"
                autoComplete="email"
                value={values.email}
                onChange={handleEmailChange}
                aria-describedby={errors.email ? emailErrorId : undefined}
                aria-invalid={errors.email ? 'true' : 'false'}
                className={errors.email ? 'field--error' : ''}
                disabled={isSubmitting}
                required
              />
            </div>
            {errors.email && (
              <span
                id={emailErrorId}
                className="field__error"
                role="alert"
                aria-live="polite"
              >
                {errors.email}
              </span>
            )}
          </div>

          <div className="auth-card__field">
            <label htmlFor={passwordId}>Password</label>
            <div className="field__input-wrapper">
              <input
                id={passwordId}
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={values.password}
                onChange={handlePasswordChange}
                aria-describedby={errors.password ? passwordErrorId : undefined}
                aria-invalid={errors.password ? 'true' : 'false'}
                className={errors.password ? 'field--error' : ''}
                disabled={isSubmitting}
                required
              />
              <button
                type="button"
                className="field__toggle-btn"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={handleTogglePassword}
                tabIndex={0}
              >
                {showPassword ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                    <line x1="1" y1="1" x2="23" y2="23" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>
            {errors.password && (
              <span
                id={passwordErrorId}
                className="field__error"
                role="alert"
                aria-live="polite"
              >
                {errors.password}
              </span>
            )}
          </div>

          <div className="auth-card__row">
            <label className="auth-card__checkbox-label" htmlFor={rememberMeId}>
              <input
                id={rememberMeId}
                type="checkbox"
                checked={values.rememberMe}
                onChange={handleRememberMeChange}
                disabled={isSubmitting}
              />
              Remember me
            </label>
            <Link to="/forgot-password" className="auth-card__link">
              Forgot password?
            </Link>
          </div>

          <button
            type="submit"
            className="btn btn--primary"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className="btn__spinner" aria-hidden="true" />}
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>
        </div>

        <p className="auth-card__footer">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="auth-card__link">
            Create account
          </Link>
        </p>
      </form>
    </div>
  );
};

export default LoginPage;
