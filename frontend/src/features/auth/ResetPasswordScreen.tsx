import { zodResolver } from '@hookform/resolvers/zod';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';
import { errorMessage } from '@/i18n';

import { resetSchema, type ResetValues } from './schemas';

/** Deep link `papeto://reset-password?token=...` (from the e-mail). Calls POST /auth/password/reset. */
export default function ResetPasswordScreen() {
  const { t } = useTranslation();
  const params = useLocalSearchParams<{ token?: string }>();
  const token = typeof params.token === 'string' ? params.token : '';
  const [serverError, setServerError] = useState<string | null>(null);
  const [tokenInvalid, setTokenInvalid] = useState(false);
  const [done, setDone] = useState(false);
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetValues>({ resolver: zodResolver(resetSchema), defaultValues: { password: '' } });
  const password = useWatch({ control, name: 'password' });

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      await api.resetPassword(token, values.password);
      setDone(true);
    } catch (error) {
      if (isApiError(error) && error.code === 'INVALID_RESET_TOKEN') setTokenInvalid(true);
      else setServerError(isApiError(error) ? errorMessage(error.code) : t('common.serverError'));
    }
  });

  if (!token || tokenInvalid) {
    return (
      <Screen
        footer={
          <Button
            testID="reset-request-new"
            label={t('auth.reset.requestNew')}
            onPress={() => router.replace('/(onboarding)/recover-password')}
          />
        }
      >
        <Text variant="title">{t('auth.reset.title')}</Text>
        <Text testID="reset-invalid" accessibilityRole="alert">
          {t('errors.INVALID_RESET_TOKEN')}
        </Text>
      </Screen>
    );
  }

  if (done) {
    return (
      <Screen
        footer={
          <Button
            testID="reset-to-sign-in"
            label={t('auth.reset.toSignIn')}
            onPress={() => router.replace('/(onboarding)/email')}
          />
        }
      >
        <Text variant="title">{t('auth.reset.doneTitle')}</Text>
        <Text accessibilityRole="alert">{t('auth.reset.done')}</Text>
      </Screen>
    );
  }

  return (
    <Screen
      footer={
        <Button
          testID="reset-submit"
          label={isSubmitting ? t('auth.reset.submitting') : t('auth.reset.submit')}
          loading={isSubmitting}
          disabled={!password}
          onPress={onSubmit}
        />
      }
    >
      <Text variant="title">{t('auth.reset.title')}</Text>
      <Text variant="secondary">{t('auth.reset.body')}</Text>
      <Controller
        control={control}
        name="password"
        render={({ field }) => (
          <TextField
            testID="reset-password"
            label={t('auth.reset.passwordLabel')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            secureToggle
            autoCapitalize="none"
            autoComplete="new-password"
            helper={t('auth.register.passwordRules')}
            error={errors.password?.message ? t(errors.password.message as never) : undefined}
          />
        )}
      />
      {serverError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {serverError}
        </Text>
      ) : null}
    </Screen>
  );
}
