import React, { useState } from 'react';
import { forgotPassword } from '../../../api/auth';

const styles = `
  :root {
    --color-accent-disabled: #c7d2fe;
    --color-accent-primary: #4f46e5;
    --color-accent-primary-active: #3730a3;
    --color-accent-primary-hover: #4338ca;
    --color-accent-secondary: #818cf8;
    --color-bg-app: #f5f3ff;
    --color-border: #e8e5ff;
    --color-border-strong: #c4b5fd;
    --color-error: #DC2626;
    --color-error-light: #fef2f2;
    --color-error-border: #fecaca;
    --color-focus-ring: #818cf8;
    --color-info: #2563EB;
    --color-link: #4f46e5;
    --color-muted-surface: #f5f3ff;
    --color-success: #16A34A;
    --color-success-light: #f0fdf4;
    --color-success-border: #bbf7d0;
    --color-surface: #ffffff;
    --color-text-muted: #94A3B8;
    --color-text-primary: #0F172A;
    --color-text-secondary: #475569;
    --color-warning: #D97706;
    --elevation-card: 0 12px 32px rgba(79,70,229,0.10);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-input: 8px;
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    --space-2xl: 48px;
  }

  .forgot-page {
    min-height: 100vh;
    background: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--family-base);
    padding: var(--space-md);
  }

  .forgot-page__branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .forgot-page__brand-name {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-accent-primary);
  }

  .auth-card {
    background: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 400px;
    border: 1px solid var(--color-border);
  }

  .auth-card__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-sm) 0;
  }

  .auth-card__subtitle {
    font-size: 14px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-xl) 0;
  }

  .auth-card__field {
    margin-bottom: var(--space-md);
  }

  .auth-card__field label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-primary);
    margin-bottom: var(--space-xs);
  }

  .auth-card__field input {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    border: 1px solid var(--color-border-strong);
    border-radius: var(--radius-input);
    font-size: 16px;
    font-family: var(--family-base);
    color: var(--color-text-primary);
    background: var(--color-surface);
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
  }

  .auth-card__field input:focus {
    border-color: var(--color-accent-primary);
    box-shadow: var(--elevation-focus);
  }

  .auth-card__field input.field--error {
    border-color: var(--color-error);
  }

  .auth-card__field input:disabled {
    background: var(--color-muted-surface);
    color: var(--color-text-muted);
    cursor: not-allowed;
  }

  .field__error {
    display: block;
    margin-top: var(--space-xs);
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-error);
  }

  .auth-card__submit {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    background: var(--color-accent-primary);
    color: var(--color-surface);
    border: none;
    border-radius: var(--radius-button);
    font-size: 16px;
    font-weight: 600;
    font-family: var(--family-base);
    cursor: pointer;
    margin-top: var(--space-md);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    transition: background 0.15s;
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

  .auth-card__submit:focus-visible {
    outline: none;
    box-shadow: var(--elevation-focus);
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: var(--color-surface);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .auth-card__banner {
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    font-size: 14px;
    line-height: 1.5;
    margin-bottom: var(--space-md);
  }

  .auth-card__banner--success {
    background: var(--color-success-light);
    color: var(--color-success);
    border: 1px solid var(--color-success-border);
  }

  .auth-card__banner--error {
    background: var(--color-error-light);
    color: var(--color-error);
    border: 1px solid var(--color-error-border);
  }

  .auth-card__footer {
    margin-top: var(--space-lg);
    text-align: center;
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .auth-card__footer a {
    color: var(--color-link);
    text-decoration: none;
    font-weight: 500;
  }

  .auth-card__footer a:hover {
    text-decoration: underline;
  }
`;

function validateEmail(email: string): string {
  if (!email.trim()) {
    return 'Email is required.';
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  if (!emailRegex.test(email)) {
    return 'Enter a valid email address.';
  }
  return '';
}

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (emailError) {
      setEmailError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const validationError = validateEmail(email);
    if (validationError) {
      setEmailError(validationError);
      return;
    }

    setIsSubmitting(true);
    setSuccessMessage('');
    setErrorMessage('');

    try {
      await forgotPassword({ email: email.trim() });
      setSuccessMessage(
        'If an account exists for that email address, you will receive a password reset link shortly.'
      );
      setEmail('');
    } catch {
      setErrorMessage(
        'Something went wrong. Please try again later.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasEmailError = Boolean(emailError);

  return (
    <>
      <style>{styles}</style>
      <div className="forgot-page">
        <div className="forgot-page__branding" aria-hidden="true">
          <span className="forgot-page__brand-name">auth-starter</span>
        </div>

        <main className="auth-card">
          <h1 className="auth-card__title">Forgot password?</h1>
          <p className="auth-card__subtitle">
            Enter your email address and we&apos;ll send you a link to reset your password.
          </p>

          <div aria-live="polite" aria-atomic="true">
            {successMessage && (
              <div className="auth-card__banner auth-card__banner--success" role="status">
                {successMessage}
              </div>
            )}
            {errorMessage && (
              <div className="auth-card__banner auth-card__banner--error" role="alert">
                {errorMessage}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className="auth-card__field">
              <label htmlFor="forgot-email">Email address</label>
              <input
                id="forgot-email"
                type="email"
                name="email"
                value={email}
                onChange={handleEmailChange}
                autoComplete="email"
                disabled={isSubmitting}
                aria-required="true"
                aria-invalid={hasEmailError}
                aria-describedby={hasEmailError ? 'forgot-email-error' : undefined}
                className={hasEmailError ? 'field--error' : ''}
                placeholder="you@example.com"
              />
              {hasEmailError && (
                <span id="forgot-email-error" className="field__error" role="alert">
                  {emailError}
                </span>
              )}
            </div>

            <button
              type="submit"
              className="auth-card__submit"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner" aria-hidden="true" />
                  Sending&hellip;
                </>
              ) : (
                'Send reset link'
              )}
            </button>
          </form>

          <div className="auth-card__footer">
            <a href="/login">Back to sign in</a>
          </div>
        </main>
      </div>
    </>
  );
};

export default ForgotPasswordPage;
