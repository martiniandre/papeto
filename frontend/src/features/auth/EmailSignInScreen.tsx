import { zodResolver } from '@hookform/resolvers/zod';
import { router } from 'expo-router';
import { useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';
import { errorMessage } from '@/i18n';

import { signInSchema, type SignInValues } from './schemas';
import { useAuthActions } from './useAuthActions';

/** Screen 21. */
export default function EmailSignInScreen() {
  const { t } = useTranslation();
  const { signIn } = useAuthActions();
  const [serverError, setServerError] = useState<string | null>(null);
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignInValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: { email: '', password: '' },
  });
  const email = useWatch({ control, name: 'email' });
  const password = useWatch({ control, name: 'password' });

  const onSubmit = handleSubmit(async (values) => {
    setServerError(null);
    try {
      await signIn(values);
    } catch (error) {
      setServerError(
        isApiError(error)
          ? error.status === 401
            ? t('auth.email.wrongPassword')
            : error.status === 429
              ? t('auth.email.tooManyAttempts')
              : errorMessage(error.code)
          : t('auth.signIn.failure'),
      );
    }
  });

  return (
    <Screen
      footer={
        <Button
          testID="email-submit"
          label={isSubmitting ? t('auth.email.submitting') : t('auth.email.submit')}
          loading={isSubmitting}
          disabled={!email || !password}
          onPress={onSubmit}
        />
      }
    >
      <Text variant="title">{t('auth.email.title')}</Text>
      <Controller
        control={control}
        name="email"
        render={({ field }) => (
          <TextField
            testID="email-input"
            label={t('auth.email.emailLabel')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            autoCapitalize="none"
            autoComplete="email"
            keyboardType="email-address"
            error={errors.email?.message ? t(errors.email.message as 'auth.email.invalidEmail') : undefined}
          />
        )}
      />
      <Controller
        control={control}
        name="password"
        render={({ field }) => (
          <TextField
            testID="password-input"
            label={t('auth.email.passwordLabel')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            autoComplete="current-password"
            secureToggle
            error={
              errors.password?.message
                ? t(errors.password.message as 'auth.email.passwordRequired')
                : undefined
            }
          />
        )}
      />
      {serverError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {serverError}
        </Text>
      ) : null}
      <View className="gap-sm">
        <Button
          action="ghost"
          label={t('auth.email.forgot')}
          onPress={() => router.push('/(onboarding)/recover-password')}
        />
        <Button
          action="ghost"
          label={t('auth.email.createAccount')}
          onPress={() => router.push('/(onboarding)/create-account')}
        />
      </View>
    </Screen>
  );
}
