import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { me, logout } from '../api/auth';

interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchProfile = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await me();
        if (!cancelled) {
          setUser(data);
        }
      } catch {
        if (!cancelled) {
          setError('Failed to load profile. Please log in again.');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    setError(null);
    try {
      await logout();
      navigate('/login', { replace: true });
    } catch {
      setError('Logout failed. Please try again.');
      setIsLoggingOut(false);
    }
  };

  return (
    <>
      <style>{`
        :root {
          --color-accent-disabled: #c7d2fe;
          --color-accent-primary: #4f46e5;
          --color-accent-primary-active: #3730a3;
          --color-accent-primary-hover: #4338ca;
          --color-bg-app: #f1f5f9;
          --color-border: #E2E8F0;
          --color-border-strong: #CBD5E1;
          --color-error: #DC2626;
          --color-focus-ring: #818cf8;
          --color-info: #2563EB;
          --color-link: #4f46e5;
          --color-muted-surface: #f8fafc;
          --color-success: #16A34A;
          --color-surface: #FFFFFF;
          --color-text-muted: #94A3B8;
          --color-text-primary: #0F172A;
          --color-text-secondary: #475569;
          --color-warning: #D97706;
          --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
          --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
          --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
          --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
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

        .profile-layout {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--space-lg);
          font-family: var(--family-base);
        }

        .profile-layout__branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .profile-layout__branding-title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-accent-primary);
          margin: 0;
          letter-spacing: -0.5px;
        }

        .profile-card {
          background-color: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-2xl);
          width: 100%;
          max-width: 480px;
          box-sizing: border-box;
        }

        .profile-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xl) 0;
          text-align: center;
        }

        .profile-card__loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-xl) 0;
          color: var(--color-text-secondary);
          font-size: 14px;
          font-weight: 500;
        }

        .profile-card__spinner {
          width: 32px;
          height: 32px;
          border: 3px solid var(--color-border);
          border-top-color: var(--color-accent-primary);
          border-radius: var(--radius-full);
          animation: profile-spin 0.7s linear infinite;
        }

        @keyframes profile-spin {
          to { transform: rotate(360deg); }
        }

        .profile-card__error {
          background-color: #fef2f2;
          border: 1px solid var(--color-error);
          border-radius: var(--radius-input);
          color: var(--color-error);
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          padding: var(--space-sm) var(--space-md);
          margin-bottom: var(--space-lg);
        }

        .profile-card__field {
          margin-bottom: var(--space-lg);
        }

        .profile-card__label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-xs);
        }

        .profile-card__value {
          font-size: 16px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-primary);
          background-color: var(--color-muted-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          display: block;
          word-break: break-all;
        }

        .profile-card__badge {
          display: inline-block;
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          padding: 2px var(--space-sm);
          border-radius: var(--radius-full);
        }

        .profile-card__badge--active {
          background-color: #dcfce7;
          color: var(--color-success);
        }

        .profile-card__badge--inactive {
          background-color: #fee2e2;
          color: var(--color-error);
        }

        .profile-card__divider {
          border: none;
          border-top: 1px solid var(--color-border);
          margin: var(--space-xl) 0;
        }

        .profile-card__logout-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          width: 100%;
          padding: var(--space-sm) var(--space-lg);
          background-color: var(--color-accent-primary);
          color: var(--color-surface);
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 500;
          line-height: 1.5;
          border: none;
          border-radius: var(--radius-button);
          cursor: pointer;
          transition: background-color 0.15s ease, box-shadow 0.15s ease;
        }

        .profile-card__logout-btn:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .profile-card__logout-btn:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .profile-card__logout-btn:focus-visible {
          outline: none;
          box-shadow: var(--elevation-focus);
        }

        .profile-card__logout-btn:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .profile-card__btn-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.4);
          border-top-color: #ffffff;
          border-radius: var(--radius-full);
          animation: profile-spin 0.7s linear infinite;
          flex-shrink: 0;
        }
      `}</style>

      <main className="profile-layout">
        <div className="profile-layout__branding" aria-label="Auth Starter">
          <h1 className="profile-layout__branding-title">Auth Starter</h1>
        </div>

        <div className="profile-card" role="main">
          <h2 className="profile-card__title">Your Profile</h2>

          {error && (
            <div
              className="profile-card__error"
              role="alert"
              aria-live="polite"
            >
              {error}
            </div>
          )}

          {isLoading && (
            <div className="profile-card__loading" aria-busy="true" aria-label="Loading profile">
              <span className="profile-card__spinner" aria-hidden="true" />
              <span>Loading profile…</span>
            </div>
          )}

          {!isLoading && user && (
            <>
              <div className="profile-card__field">
                <span className="profile-card__label" id="label-full-name">Full Name</span>
                <span
                  className="profile-card__value"
                  aria-labelledby="label-full-name"
                >
                  {user.full_name}
                </span>
              </div>

              <div className="profile-card__field">
                <span className="profile-card__label" id="label-email">Email</span>
                <span
                  className="profile-card__value"
                  aria-labelledby="label-email"
                >
                  {user.email}
                </span>
              </div>

              <div className="profile-card__field">
                <span className="profile-card__label" id="label-status">Account Status</span>
                <span
                  className={`profile-card__badge ${
                    user.is_active
                      ? 'profile-card__badge--active'
                      : 'profile-card__badge--inactive'
                  }`}
                  aria-labelledby="label-status"
                >
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>

              <div className="profile-card__field">
                <span className="profile-card__label" id="label-member-since">Member Since</span>
                <span
                  className="profile-card__value"
                  aria-labelledby="label-member-since"
                >
                  {new Date(user.created_at).toLocaleDateString(undefined, {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </span>
              </div>

              <hr className="profile-card__divider" aria-hidden="true" />

              <button
                type="button"
                className="profile-card__logout-btn"
                onClick={handleLogout}
                disabled={isLoggingOut}
                aria-busy={isLoggingOut}
              >
                {isLoggingOut && (
                  <span className="profile-card__btn-spinner" aria-hidden="true" />
                )}
                {isLoggingOut ? 'Signing out…' : 'Sign Out'}
              </button>
            </>
          )}
        </div>
      </main>
    </>
  );
};

export default ProfilePage;
