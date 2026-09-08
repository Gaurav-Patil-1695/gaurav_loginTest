import { useState, useCallback, ChangeEvent, FocusEvent, FormEvent } from 'react';

export type FieldValues = Record<string, string>;
export type FieldErrors = Record<string, string>;
export type FieldTouched = Record<string, boolean>;

export type Validator<T extends FieldValues> = (
  values: T
) => Partial<Record<keyof T, string>>;

export interface UseAuthFormOptions<T extends FieldValues> {
  initialValues: T;
  validate: Validator<T>;
  onSubmit: (values: T) => Promise<void>;
}

export interface UseAuthFormReturn<T extends FieldValues> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isSubmitting: boolean;
  submitError: string;
  submitSuccess: boolean;
  handleChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleBlur: (e: FocusEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  setFieldValue: (name: keyof T, value: string) => void;
  resetForm: () => void;
}

function useAuthForm<T extends FieldValues>({
  initialValues,
  validate,
  onSubmit,
}: UseAuthFormOptions<T>): UseAuthFormReturn<T> {
  const [values, setValues] = useState<T>({ ...initialValues });
  const [errors, setErrors] = useState<Partial<Record<keyof T, string>>>({});
  const [touched, setTouched] = useState<Partial<Record<keyof T, boolean>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setValues((prev) => ({ ...prev, [name]: value }));
      setErrors((prev) => {
        if (!prev[name as keyof T]) return prev;
        const updated = { ...prev };
        delete updated[name as keyof T];
        return updated;
      });
    },
    []
  );

  const handleBlur = useCallback(
    (e: FocusEvent<HTMLInputElement>) => {
      const { name } = e.target;
      setTouched((prev) => ({ ...prev, [name]: true }));
      setValues((current) => {
        const fieldErrors = validate(current);
        setErrors((prev) => ({
          ...prev,
          ...(fieldErrors[name as keyof T] !== undefined
            ? { [name]: fieldErrors[name as keyof T] }
            : {}),
        }));
        return current;
      });
    },
    [validate]
  );

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      const allTouched = Object.keys(values).reduce<
        Partial<Record<keyof T, boolean>>
      >((acc, key) => {
        acc[key as keyof T] = true;
        return acc;
      }, {});
      setTouched(allTouched);

      const fieldErrors = validate(values);
      const hasErrors = Object.values(fieldErrors).some(
        (msg) => msg !== undefined && msg !== ''
      );

      if (hasErrors) {
        setErrors(fieldErrors as Partial<Record<keyof T, string>>);
        return;
      }

      setErrors({});
      setSubmitError('');
      setSubmitSuccess(false);
      setIsSubmitting(true);

      try {
        await onSubmit(values);
        setSubmitSuccess(true);
      } catch (err: unknown) {
        const message =
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred. Please try again.';
        setSubmitError(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validate, onSubmit]
  );

  const setFieldValue = useCallback((name: keyof T, value: string) => {
    setValues((prev) => ({ ...prev, [name]: value }));
  }, []);

  const resetForm = useCallback(() => {
    setValues({ ...initialValues });
    setErrors({});
    setTouched({});
    setIsSubmitting(false);
    setSubmitError('');
    setSubmitSuccess(false);
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    submitSuccess,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    resetForm,
  };
}

export default useAuthForm;
