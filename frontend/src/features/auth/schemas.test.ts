import { registerSchema, signInSchema } from './schemas';

describe('auth schemas', () => {
  it('validates the email', () => {
    expect(signInSchema.safeParse({ email: 'nope', password: 'x' }).success).toBe(false);
    expect(signInSchema.safeParse({ email: ' ana@example.com ', password: 'x' }).success).toBe(true);
  });

  it('rejects weak passwords with the i18n key', () => {
    const result = registerSchema.safeParse({ name: 'Ana', email: 'ana@example.com', password: 'abcdefgh', adult: true });
    expect(result.success).toBe(false);
    expect(result.error?.issues[0]?.message).toBe('auth.register.weakPassword');
    expect(
      registerSchema.safeParse({ name: 'Ana', email: 'ana@example.com', password: 'abcd1234', adult: true }).success,
    ).toBe(true);
  });
});
