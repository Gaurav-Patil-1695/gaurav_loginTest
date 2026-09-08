import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { resetPassword } from '../../../api/auth';

const STYLES = `
  :root {
    --color-accent-disabled: #c7d2fe;
    --color-accent-primary: #4f46e5;
    --color-accent-primary-active: #3730a3;
    --color-accent-primary-hover: #4338ca;
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
    --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
    --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
    --elevation-card: 0 12px 32px rgba(79,70,229,0.10);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-full: 9999px;
    --radius-input: 8px;
    --radius-sm: 4px;
    --space-2xl: 48px;
    --space-lg: 24px;
    --space-md: 16px;
    --space-sm: 8px;
    --space-xl: 32px;
    --space-xs: 4px;
  }

  .rp-app {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    font-family: var(--family-base);
    padding: var(--space-md);
  }

  .rp-branding {
    margin-bottom: var(--space-lg);
    text-align: center;
  }

  .rp-branding__logo {
    width: 48px;
    height: 48px;
    background-color: var(--color-accent-primary);
    border-radius: var(--radius-lg, 12px);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: var(--space-sm);
  }

  .rp-branding__logo svg {
    width: 28px;
    height: 28px;
    fill: var(--color-surface);
  }

  .rp-branding__name {
    font-size: 18px;
    font-weight: 600;
    line-height: 1.25;
    color: var(--color-text-primary);
    margin: 0;
  }

  .auth-card {
    background-color: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    border: 1px solid var(--color-border);
    padding: var(--space-xl);
    width: 100%;
    max-width: 400px;
  }

  .auth-card__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-xs) 0;
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

  .auth-card__input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .auth-card__input {
    width: 100%;
    padding: 10px var(--space-md);
    font-size: 16px;
    font-family: var(--family-base);
    line-height: 1.5;
    color: var(--color-text-primary);
    background-color: var(--color-surface);
    border: 1.5px solid var(--color-border-strong);
    border-radius: var(--radius-input);
    box-sizing: border-box;
    outline: none;
    transition: border-color 0.15s, box-shadow 0.15s;
    padding-right: 44px;
  }

  .auth-card__input:focus {
    border-color: var(--color-accent-primary);
    box-shadow: var(--elevation-focus);
  }

  .auth-card__input.field--error {
    border-color: var(--color-error);
  }

  .auth-card__input:disabled {
    background-color: var(--color-muted-surface);
    color: var(--color-text-muted);
    cursor: not-allowed;
  }

  .auth-card__eye-btn {
    position: absolute;
    right: var(--space-sm);
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    padding: var(--space-xs);
    cursor: pointer;
    color: var(--color-text-muted);
    display: flex;
    align-items: center;
    border-radius: var(--radius-sm);
    transition: color 0.15s;
  }

  .auth-card__eye-btn:hover {
    color: var(--color-text-secondary);
  }

  .auth-card__eye-btn:focus-visible {
    outline: 2px solid var(--color-focus-ring);
    outline-offset: 2px;
  }

  .field--error-msg {
    display: block;
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-error);
    margin-top: var(--space-xs);
  }

  .auth-card__strength {
    margin-top: var(--space-sm);
  }

  .auth-card__strength-bar {
    display: flex;
    gap: var(--space-xs);
    margin-bottom: var(--space-xs);
  }

  .auth-card__strength-segment {
    flex: 1;
    height: 4px;
    border-radius: var(--radius-full);
    background-color: var(--color-border);
    transition: background-color 0.2s;
  }

  .auth-card__strength-segment--active-1 {
    background-color: var(--color-error);
  }

  .auth-card__strength-segment--active-2 {
    background-color: var(--color-warning);
  }

  .auth-card__strength-segment--active-3 {
    background-color: var(--color-info);
  }

  .auth-card__strength-segment--active-4 {
    background-color: var(--color-success);
  }

  .auth-card__strength-label {
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-text-muted);
  }

  .auth-card__strength-label--1 { color: var(--color-error); }
  .auth-card__strength-label--2 { color: var(--color-warning); }
  .auth-card__strength-label--3 { color: var(--color-info); }
  .auth-card__strength-label--4 { color: var(--color-success); }

  .auth-card__submit {
    width: 100%;
    padding: 11px var(--space-md);
    font-size: 16px;
    font-weight: 600;
    font-family: var(--family-base);
    color: var(--color-surface);
    background-color: var(--color-accent-primary);
    border: none;
    border-radius: var(--radius-button);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    transition: background-color 0.15s;
    margin-top: var(--space-xl);
    box-sizing: border-box;
  }

  .auth-card__submit:hover:not(:disabled) {
    background-color: var(--color-accent-primary-hover);
  }

  .auth-card__submit:active:not(:disabled) {
    background-color: var(--color-accent-primary-active);
  }

  .auth-card__submit:disabled {
    background-color: var(--color-accent-disabled);
    cursor: not-allowed;
  }

  .auth-card__submit:focus-visible {
    outline: 2px solid var(--color-focus-ring);
    outline-offset: 2px;
  }

  .auth-card__spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255,255,255,0.35);
    border-top-color: var(--color-surface);
    border-radius: var(--radius-full);
    animation: rp-spin 0.7s linear infinite;
    flex-shrink: 0;
  }

  @keyframes rp-spin {
    to { transform: rotate(360deg); }
  }

  .auth-card__banner {
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    margin-bottom: var(--space-md);
  }

  .auth-card__banner--error {
    background-color: var(--color-error-light);
    color: var(--color-error);
    border: 1px solid var(--color-error-border);
  }

  .auth-card__banner--success {
    background-color: var(--color-success-light);
    color: var(--color-success);
    border: 1px solid var(--color-success-border);
  }

  .auth-card__footer {
    margin-top: var(--space-lg);
    text-align: center;
    font-size: 14px;
    font-weight: 500;
    color: var(--color-text-secondary);
  }

  .auth-card__link {
    color: var(--color-link);
    text-decoration: none;
    font-weight: 500;
  }

  .auth-card__link:hover {
    text-decoration: underline;
  }

  .auth-card__link:focus-visible {
    outline: 2px solid var(--color-focus-ring);
    outline-offset: 2px;
    border-radius: var(--radius-sm);
  }

  .auth-card__invalid-token {
    text-align: center;
    padding: var(--space-lg) 0;
  }

  .auth-card__invalid-token p {
    font-size: 14px;
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-md) 0;
  }
`;

function validatePassword(value: string): string | null {
  if (!value) return 'Password is required.';
  if (value.length < 8) return 'Password must be at least 8 characters.';
  if (!/[A-Z]/.test(value)) return 'Password must contain at least one uppercase letter.';
  if (!/[a-z]/.test(value)) return 'Password must contain at least one lowercase letter.';
  if (!/[0-9]/.test(value)) return 'Password must contain at least one number.';
  return null;
}

function validateConfirmPassword(password: string, confirm: string): string | null {
  if (!confirm) return 'Please confirm your password.';
  if (password !== confirm) return 'Passwords do not match.';
  return null;
}

function getPasswordStrength(value: string): number {
  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value)) score++;
  if (/[a-z]/.test(value)) score++;
  if (/[0-9]/.test(value)) score++;
  return score;
}

const STRENGTH_LABELS: Record<number, string> = {
  0: '',
  1: 'Weak',
  2: 'Fair',
  3: 'Good',
  4: 'Strong',
};

interface FormState {
  password: string;
  confirmPassword: string;
}

interface FormErrors {
  password: string | null;
  confirmPassword: string | null;
}

const ResetPasswordPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token') ?? '';

  const [form, setForm] = useState<FormState>({
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<FormErrors>({
    password: null,
    confirmPassword: null,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [banner, setBanner] = useState<{ type: 'error' | 'success'; message: string } | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  useEffect(() => {
    if (!token) {
      setBanner({ type: 'error', message: 'Reset token is missing or invalid. Please request a new password reset link.' });
    }
  }, [token]);

  const handleChange = (field: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setForm(prev => ({ ...prev, [field]: value }));
    setBanner(null);
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleBlur = (field: keyof FormState) => () => {
    if (field === 'password') {
      setErrors(prev => ({ ...prev, password: validatePassword(form.password) }));
    }
    if (field === 'confirmPassword') {
      setErrors(prev => ({
        ...prev,
        confirmPassword: validateConfirmPassword(form.password, form.confirmPassword),
      }));
    }
  };

  const validate = (): boolean => {
    const passwordErr = validatePassword(form.password);
    const confirmErr = validateConfirmPassword(form.password, form.confirmPassword);
    setErrors({ password: passwordErr, confirmPassword: confirmErr });
    return !passwordErr && !confirmErr;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;
    if (!token) {
      setBanner({ type: 'error', message: 'Reset token is missing or invalid. Please request a new password reset link.' });
      return;
    }
    setIsSubmitting(true);
    setBanner(null);
    try {
      await resetPassword({ token, newPassword: form.password, confirmPassword: form.confirmPassword });
      setIsSuccess(true);
      setBanner({ type: 'success', message: 'Your password has been reset successfully.' });
    } catch (err: unknown) {
      const apiError = err as { response?: { data?: { error?: { message?: string } } } };
      const message =
        apiError?.response?.data?.error?.message ??
        'Something went wrong. Please try again or request a new reset link.';
      setBanner({ type: 'error', message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const passwordStrength = getPasswordStrength(form.password);
  const showStrength = form.password.length > 0;

  const passwordFieldId = 'rp-password';
  const passwordErrorId = 'rp-password-error';
  const confirmFieldId = 'rp-confirm-password';
  const confirmErrorId = 'rp-confirm-password-error';
  const bannerId = 'rp-banner';

  return (
    <>
      <style>{STYLES}</style>
      <div className="rp-app">
        <div className="rp-branding" aria-label="App branding">
          <div className="rp-branding__logo" aria-hidden="true">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 1a5 5 0 0 1 5 5v2h1a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V10a2 2 0 0 1 2-2h1V6a5 5 0 0 1 5-5zm0 2a3 3 0 0 0-3 3v2h6V6a3 3 0 0 0-3-3zm0 8a2 2 0 1 0 0 4 2 2 0 0 0 0-4z" />
            </svg>
          </div>
          <p className="rp-branding__name">auth-starter</p>
        </div>

        <main className="auth-card" role="main">
          <h1 className="auth-card__title">Set new password</h1>
          <p className="auth-card__subtitle">Choose a strong password for your account.</p>

          <div aria-live="polite" aria-atomic="true">
            {banner && (
              <div
                id={bannerId}
                className={`auth-card__banner auth-card__banner--${banner.type}`}
                role={banner.type === 'error' ? 'alert' : 'status'}
              >
                {banner.message}
              </div>
            )}
          </div>

          {isSuccess ? (
            <div className="auth-card__invalid-token">
              <p>You can now sign in with your new password.</p>
              <Link to="/login" className="auth-card__link">Go to Sign In</Link>
            </div>
          ) : !token ? (
            <div className="auth-card__invalid-token">
              <p>Please request a new password reset link to continue.</p>
              <Link to="/forgot-password" className="auth-card__link">Request new link</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} noValidate>
              <div className="auth-card__field">
                <label htmlFor={passwordFieldId}>New Password</label>
                <div className="auth-card__input-wrapper">
                  <input
                    id={passwordFieldId}
                    type={showPassword ? 'text' : 'password'}
                    className={`auth-card__input${errors.password ? ' field--error' : ''}`}
                    value={form.password}
                    onChange={handleChange('password')}
                    onBlur={handleBlur('password')}
                    autoComplete="new-password"
                    disabled={isSubmitting}
                    aria-required="true"
                    aria-describedby={
                      errors.password ? passwordErrorId : undefined
                    }
                    aria-invalid={errors.password ? 'true' : 'false'}
                  />
                  <button
                    type="button"
                    className="auth-card__eye-btn"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPassword(prev => !prev)}
                    tabIndex={0}
                  >
                    {showPassword ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
                {errors.password && (
                  <span id={passwordErrorId} className="field--error-msg" role="alert">
                    {errors.password}
                  </span>
                )}
                {showStrength && (
                  <div className="auth-card__strength" aria-label={`Password strength: ${STRENGTH_LABELS[passwordStrength]}`}>
                    <div className="auth-card__strength-bar" aria-hidden="true">
                      {[1, 2, 3, 4].map(seg => (
                        <div
                          key={seg}
                          className={`auth-card__strength-segment${
                            passwordStrength >= seg
                              ? ` auth-card__strength-segment--active-${passwordStrength}`
                              : ''
                          }`}
                        />
                      ))}
                    </div>
                    {passwordStrength > 0 && (
                      <span className={`auth-card__strength-label auth-card__strength-label--${passwordStrength}`}>
                        {STRENGTH_LABELS[passwordStrength]}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="auth-card__field">
                <label htmlFor={confirmFieldId}>Confirm New Password</label>
                <div className="auth-card__input-wrapper">
                  <input
                    id={confirmFieldId}
                    type={showConfirm ? 'text' : 'password'}
                    className={`auth-card__input${errors.confirmPassword ? ' field--error' : ''}`}
                    value={form.confirmPassword}
                    onChange={handleChange('confirmPassword')}
                    onBlur={handleBlur('confirmPassword')}
                    autoComplete="new-password"
                    disabled={isSubmitting}
                    aria-required="true"
                    aria-describedby={
                      errors.confirmPassword ? confirmErrorId : undefined
                    }
                    aria-invalid={errors.confirmPassword ? 'true' : 'false'}
                  />
                  <button
                    type="button"
                    className="auth-card__eye-btn"
                    aria-label={showConfirm ? 'Hide confirm password' : 'Show confirm password'}
                    onClick={() => setShowConfirm(prev => !prev)}
                    tabIndex={0}
                  >
                    {showConfirm ? (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                        <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                        <line x1="1" y1="1" x2="23" y2="23" />
                      </svg>
                    ) : (
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                        <circle cx="12" cy="12" r="3" />
                      </svg>
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <span id={confirmErrorId} className="field--error-msg" role="alert">
                    {errors.confirmPassword}
                  </span>
                )}
              </div>

              <button
                type="submit"
                className="auth-card__submit"
                disabled={isSubmitting}
                aria-busy={isSubmitting}
              >
                {isSubmitting && <span className="auth-card__spinner" aria-hidden="true" />}
                {isSubmitting ? 'Resetting…' : 'Reset Password'}
              </button>
            </form>
          )}

          <div className="auth-card__footer">
            <Link to="/login" className="auth-card__link">Back to Sign In</Link>
          </div>
        </main>
      </div>
    </>
  );
};

export default ResetPasswordPage;
