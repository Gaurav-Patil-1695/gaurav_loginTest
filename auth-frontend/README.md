# auth-frontend

React + TypeScript single-page application that provides the authentication UI for the auth-starter project. It communicates with the `auth-backend` FastAPI service through a Vite dev proxy (in development) or directly via `VITE_API_BASE_URL` (in production builds).

---

## Tech stack

| Tool | Version | Purpose |
|---|---|---|
| React | 18 | UI rendering |
| TypeScript | 5 | Static typing |
| Vite | 5 | Dev server and bundler |
| React Router DOM | 6 | Client-side routing |
| Vitest | 2 | Unit tests |
| ESLint | 8 | Linting |

---

## Project structure

```
auth-frontend/
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite config (proxy, plugins)
├── tsconfig.json               # TypeScript config
├── package.json
├── .env.example                # Required env variables
└── src/
    ├── main.tsx                # React DOM root
    ├── App.tsx                 # Router + route guards
    ├── api/
    │   └── auth.ts             # API client (login, register, me, …)
    ├── context/
    │   └── AuthContext.tsx     # Global auth state
    ├── hooks/
    │   └── useAuthForm.ts      # Controlled-form + validation hook
    ├── features/
    │   └── auth/
    │       └── pages/
    │           ├── LoginPage.tsx
    │           ├── RegisterPage.tsx
    │           ├── ForgotPasswordPage.tsx
    │           └── ResetPasswordPage.tsx
    ├── pages/
    │   └── ProfilePage.tsx
    ├── components/
    │   ├── RequireAuth.tsx     # Redirects unauthenticated users
    │   └── RequireGuest.tsx    # Redirects already-authenticated users
    └── styles/
        └── tokens.css          # CSS custom properties from design tokens
```

---

## Environment variables

Copy `.env.example` to `.env` (or `.env.local`) before running the app. Vite only
exposes variables prefixed with `VITE_` to browser code.

| Variable | Required | Default (example) | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | Base URL of the `auth-backend` service. Used by the API client for all `/api/v1/*` requests. In development the Vite proxy forwards `/api/v1` to this origin automatically. In a production build this value is baked into the bundle at build time. |

### Creating your local `.env`

```bash
cp .env.example .env
# Edit .env and set VITE_API_BASE_URL if your backend runs on a different port
```

> **Note** — Never commit `.env` or `.env.local` to version control. Both files
> are listed in the root `.gitignore`.

---

## Setup and development

### Prerequisites

- Node.js ≥ 20
- npm ≥ 10 (or `pnpm` / `yarn` — adjust commands accordingly)
- The `auth-backend` service running on `http://localhost:8000` (see the backend
  `README.md` or `docker-compose.yml` at the repo root)

### Install dependencies

```bash
cd auth-frontend
npm install
```

### Start the dev server

```bash
npm run dev
```

Vite starts on **http://localhost:5173** and proxies every `/api/v1/*` request to
`http://localhost:8000`, so CORS is transparent during development.

### Build for production

```bash
npm run build
```

Output is written to `auth-frontend/dist/`. Serve the `dist/` folder with any
static file host (Nginx, Caddy, Netlify, Vercel, etc.).

> Ensure `VITE_API_BASE_URL` is set to your production backend URL **before**
> running the build command, because Vite inlines the value at build time.

### Preview the production build locally

```bash
npm run build
npx vite preview
```

---

## Running tests

```bash
npm test
```

Runs Vitest in non-interactive (CI) mode. Tests cover:

- Validation rules — asserts the exact error messages defined in
  `validation-rules.json`
- Route guards (`RequireAuth`, `RequireGuest`) — verifies redirect behaviour

---

## Linting

```bash
npm run lint
```

Runs ESLint with the React + React Hooks + TypeScript plugins. Zero warnings are
allowed (`--max-warnings 0`).

---

## Available routes

| Path | Component | Guard |
|---|---|---|
| `/login` | `LoginPage` | `RequireGuest` — redirects to `/profile` if already authenticated |
| `/register` | `RegisterPage` | `RequireGuest` |
| `/forgot-password` | `ForgotPasswordPage` | `RequireGuest` |
| `/reset-password` | `ResetPasswordPage` | `RequireGuest` |
| `/profile` | `ProfilePage` | `RequireAuth` — redirects to `/login` if unauthenticated |

---

## API endpoints consumed

All requests are sent to `VITE_API_BASE_URL` via the client defined in
`src/api/auth.ts`.

| Method | Path | Handler | Description |
|---|---|---|---|
| `POST` | `/auth/register` | `register` | Create a new account |
| `POST` | `/auth/login` | `login` | Obtain access + refresh tokens |
| `GET` | `/auth/me` | `me` | Fetch the authenticated user's profile |
| `POST` | `/auth/logout` | `logout` | Revoke the current refresh token |
| `POST` | `/auth/refresh` | `refresh` | Rotate the refresh token |
| `POST` | `/auth/forgot-password` | `forgotPassword` | Request a password-reset email |
| `POST` | `/auth/reset-password` | `resetPassword` | Set a new password using a reset token |

---

## Running with Docker Compose

From the **repository root**:

```bash
docker-compose up --build
```

This starts both `auth-backend` and `auth-frontend` (served by Nginx on port
**3000**). See `docker-compose.yml` for port mappings and service names.

---

## Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `VITE_API_BASE_URL is not defined` error in browser console | `.env` file missing or variable not prefixed with `VITE_` | Copy `.env.example` to `.env` and verify the variable name |
| 404 on API calls in production | `VITE_API_BASE_URL` not set before `npm run build` | Rebuild after exporting the correct variable |
| TypeScript errors after `npm install` | Node version below 20 | Upgrade Node.js |
| ESLint reports unused variables | Strict mode is on | Remove or prefix with `_` as appropriate |
