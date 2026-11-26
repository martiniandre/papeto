import { zodResolver } from '@hookform/resolvers/zod';
import { router } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Checkbox } from '@/components/ui/Checkbox';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';
import { errorMessage } from '@/i18n';

import { registerSchema, type RegisterValues } from './schemas';
import { useAuthActions } from './useAuthActions';

/** Screen 22. */
export default function CreateAccountScreen() {
  const { t } = useTranslation();
  const { register } = useAuthActions();
  const [serverError, setServerError] = useState<string | null>(null);
  const [emailTaken, setEmailTaken] = useState(false);
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: '', email: '', password: '', adult: false },
  });
  const values = useWatch({ control });
  const msg = (key?: string) => (key ? (t as (k: string) => string)(key) : undefined);

  const onSubmit = handleSubmit(async (input) => {
    setServerError(null);
    setEmailTaken(false);
    try {
      await register({
        name: input.name,
        email: input.email,
        password: input.password,
        adult_confirmed: input.adult,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
    } catch (error) {
      if (isApiError(error) && (error.code === 'EMAIL_ALREADY_REGISTERED' || error.status === 409)) {
        setEmailTaken(true);
        setServerError(t('auth.register.emailTaken'));
      } else {
        setServerError(isApiError(error) ? errorMessage(error.code) : t('common.serverError'));
      }
    }
  });

  return (
    <Screen
      footer={
        <Button
          testID="register-submit"
          label={isSubmitting ? t('auth.register.submitting') : t('auth.register.submit')}
          loading={isSubmitting}
          disabled={!values.name || !values.email || !values.password || !values.adult}
          onPress={onSubmit}
        />
      }
    >
      <Text variant="title">{t('auth.register.title')}</Text>
      <Controller
        control={control}
        name="name"
        render={({ field }) => (
          <TextField
            label={t('auth.register.nameLabel')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            autoComplete="name"
            error={msg(errors.name?.message)}
          />
        )}
      />
      <Controller
        control={control}
        name="email"
        render={({ field }) => (
          <TextField
            label={t('auth.email.emailLabel')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            error={msg(errors.email?.message)}
          />
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field }) => (
          <TextField
            label={t('auth.email.passwordLabel')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            autoComplete="new-password"
            secureToggle
            helper={t('auth.register.passwordRules')}
            error={msg(errors.password?.message)}
          />
        )}
      />
      <Controller
        control={control}
        name="adult"
        render={({ field }) => (
          <Checkbox
            testID="register-adult"
            label={t('auth.register.adultCheckbox')}
            checked={field.value}
            onChange={field.onChange}
          />
        )}
      />
      {errors.adult?.message ? (
        <Text accessibilityRole="alert">{msg(errors.adult.message)}</Text>
      ) : null}
      {serverError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {serverError}
        </Text>
      ) : null}
      {emailTaken ? (
        <Button
          action="ghost"
          label={t('auth.register.goToSignIn')}
          onPress={() => router.replace('/(onboarding)/email')}
        />
      ) : null}
    </Screen>
  );
}
