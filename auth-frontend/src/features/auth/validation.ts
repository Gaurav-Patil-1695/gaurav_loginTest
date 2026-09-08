// Client-side mirror of validation-rules.md
// Rule order and exact messages match the server-side rules verbatim.

// Password policy (mirrored from config: capabilities.yaml)
const PASSWORD_MIN_LENGTH = 8;
const PASSWORD_REQUIRE_UPPERCASE = true;
const PASSWORD_REQUIRE_LOWERCASE = true;
const PASSWORD_REQUIRE_NUMBER = true;
const PASSWORD_REQUIRE_SPECIAL = false;

export interface ValidationResult {
  valid: boolean;
  message: string | null;
}

export interface PasswordStrength {
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  score: number; // 0-4
}

// ---------------------------------------------------------------------------
// Individual field validators
// ---------------------------------------------------------------------------

export function validateFullName(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Full name is required.' };
  }
  if (value.trim().length < 2) {
    return { valid: false, message: 'Full name must be at least 2 characters.' };
  }
  if (value.trim().length > 100) {
    return { valid: false, message: 'Full name must not exceed 100 characters.' };
  }
  return { valid: true, message: null };
}

export function validateEmail(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Email is required.' };
  }
  // RFC-5321 simplified pattern
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value.trim())) {
    return { valid: false, message: 'Enter a valid email address.' };
  }
  return { valid: true, message: null };
}

export function validatePassword(value: string): ValidationResult {
  if (!value) {
    return { valid: false, message: 'Password is required.' };
  }
  if (value.length < PASSWORD_MIN_LENGTH) {
    return {
      valid: false,
      message: `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`,
    };
  }
  if (PASSWORD_REQUIRE_UPPERCASE && !/[A-Z]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one uppercase letter.',
    };
  }
  if (PASSWORD_REQUIRE_LOWERCASE && !/[a-z]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one lowercase letter.',
    };
  }
  if (PASSWORD_REQUIRE_NUMBER && !/[0-9]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one number.',
    };
  }
  if (PASSWORD_REQUIRE_SPECIAL && !/[^A-Za-z0-9]/.test(value)) {
    return {
      valid: false,
      message: 'Password must contain at least one special character.',
    };
  }
  return { valid: true, message: null };
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): ValidationResult {
  if (!confirmPassword) {
    return { valid: false, message: 'Please confirm your password.' };
  }
  if (password !== confirmPassword) {
    return { valid: false, message: 'Passwords do not match.' };
  }
  return { valid: true, message: null };
}

export function validateTerms(accepted: boolean): ValidationResult {
  if (!accepted) {
    return {
      valid: false,
      message: 'You must accept the Terms of Service to register.',
    };
  }
  return { valid: true, message: null };
}

export function validateResetToken(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Reset token is required.' };
  }
  return { valid: true, message: null };
}

// ---------------------------------------------------------------------------
// Form-level validators (run all rules, return map of field -> message)
// ---------------------------------------------------------------------------

export interface LoginErrors {
  email?: string;
  password?: string;
}

export function validateLoginForm(values: {
  email: string;
  password: string;
}): LoginErrors {
  const errors: LoginErrors = {};

  const emailResult = validateEmail(values.email);
  if (!emailResult.valid) errors.email = emailResult.message!;

  if (!values.password) {
    errors.password = 'Password is required.';
  }

  return errors;
}

export interface RegisterErrors {
  full_name?: string;
  email?: string;
  password?: string;
  confirm_password?: string;
  terms?: string;
}

export function validateRegisterForm(values: {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  terms: boolean;
}): RegisterErrors {
  const errors: RegisterErrors = {};

  const fullNameResult = validateFullName(values.full_name);
  if (!fullNameResult.valid) errors.full_name = fullNameResult.message!;

  const emailResult = validateEmail(values.email);
  if (!emailResult.valid) errors.email = emailResult.message!;

  const passwordResult = validatePassword(values.password);
  if (!passwordResult.valid) errors.password = passwordResult.message!;

  const confirmResult = validateConfirmPassword(
    values.password,
    values.confirm_password,
  );
  if (!confirmResult.valid) errors.confirm_password = confirmResult.message!;

  const termsResult = validateTerms(values.terms);
  if (!termsResult.valid) errors.terms = termsResult.message!;

  return errors;
}

export interface ForgotPasswordErrors {
  email?: string;
}

export function validateForgotPasswordForm(values: {
  email: string;
}): ForgotPasswordErrors {
  const errors: ForgotPasswordErrors = {};

  const emailResult = validateEmail(values.email);
  if (!emailResult.valid) errors.email = emailResult.message!;

  return errors;
}

export interface ResetPasswordErrors {
  token?: string;
  password?: string;
  confirm_password?: string;
}

export function validateResetPasswordForm(values: {
  token: string;
  password: string;
  confirm_password: string;
}): ResetPasswordErrors {
  const errors: ResetPasswordErrors = {};

  const tokenResult = validateResetToken(values.token);
  if (!tokenResult.valid) errors.token = tokenResult.message!;

  const passwordResult = validatePassword(values.password);
  if (!passwordResult.valid) errors.password = passwordResult.message!;

  const confirmResult = validateConfirmPassword(
    values.password,
    values.confirm_password,
  );
  if (!confirmResult.valid) errors.confirm_password = confirmResult.message!;

  return errors;
}

// ---------------------------------------------------------------------------
// Password strength meter (four active rules only; special char NOT required)
// ---------------------------------------------------------------------------

export function getPasswordStrength(value: string): PasswordStrength {
  const hasMinLength = value.length >= PASSWORD_MIN_LENGTH;
  const hasUppercase = /[A-Z]/.test(value);
  const hasLowercase = /[a-z]/.test(value);
  const hasNumber = /[0-9]/.test(value);

  const score = [hasMinLength, hasUppercase, hasLowercase, hasNumber].filter(
    Boolean,
  ).length;

  return {
    hasMinLength,
    hasUppercase,
    hasLowercase,
    hasNumber,
    score,
  };
}

export function isFormValid<T extends Record<string, string | undefined>>(
  errors: T,
): boolean {
  return Object.values(errors).every((v) => v === undefined);
}
