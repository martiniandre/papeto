import { z } from 'zod';

/**
 * Form schemas. Messages are i18n keys, translated by the screen.
 * ASSUMPTION: password policy (8+ chars, letters and digits) is not defined in docs;
 * the backend remains the authority.
 */
export const PASSWORD_MIN = 8;

const email = z.string().trim().email('auth.email.invalidEmail');

export const signInSchema = z.object({
  email,
  password: z.string().min(1, 'auth.email.passwordRequired'),
});

export const registerSchema = z.object({
  name: z.string().trim().min(1, 'auth.register.nameRequired'),
  email,
  password: z
    .string()
    .min(PASSWORD_MIN, 'auth.register.weakPassword')
    .regex(/[A-Za-z]/, 'auth.register.weakPassword')
    .regex(/\d/, 'auth.register.weakPassword'),
  adult: z.boolean().refine((value) => value, 'auth.register.adultRequired'),
});

export const resetSchema = z.object({
  password: z
    .string()
    .min(PASSWORD_MIN, 'auth.register.weakPassword')
    .regex(/[A-Za-z]/, 'auth.register.weakPassword')
    .regex(/\d/, 'auth.register.weakPassword'),
});

export const recoverSchema = z.object({ email });

export type SignInValues = z.infer<typeof signInSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
export type ResetValues = z.infer<typeof resetSchema>;
export type RecoverValues = z.infer<typeof recoverSchema>;
