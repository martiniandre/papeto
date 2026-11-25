import { zodResolver } from '@hookform/resolvers/zod';
import { useState } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';

import { api } from '@/api/endpoints';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';

import { recoverSchema, type RecoverValues } from './schemas';

/** Screen 23. The "sent" message is the same whether or not the email exists. */
export default function RecoverPasswordScreen() {
  const { t } = useTranslation();
  const [sent, setSent] = useState(false);
  const {
    control,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RecoverValues>({
    resolver: zodResolver(recoverSchema),
    defaultValues: { email: '' },
  });
  const email = watch('email');

  const onSubmit = handleSubmit(async ({ email: value }) => {
    try {
      await api.forgotPassword(value);
    } catch {
      // Same message regardless of the outcome (no account enumeration).
    }
    setSent(true);
  });

  return (
    <Screen
      footer={
        sent ? null : (
          <Button
            label={isSubmitting ? t('auth.recover.submitting') : t('auth.recover.submit')}
            loading={isSubmitting}
            disabled={!email}
            onPress={onSubmit}
          />
        )
      }
    >
      <Text variant="title">{t('auth.recover.title')}</Text>
      {sent ? (
        <Text accessibilityRole="alert">{t('auth.recover.sent')}</Text>
      ) : (
        <>
          <Text variant="secondary">{t('auth.recover.body')}</Text>
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
                error={errors.email?.message ? t('auth.email.invalidEmail') : undefined}
              />
            )}
          />
        </>
      )}
    </Screen>
  );
}
