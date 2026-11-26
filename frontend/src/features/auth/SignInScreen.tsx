import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Logo } from '@/components/Logo';
import { Pet } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

type Provider = 'apple' | 'google';

/**
 * Screen 1. Email goes to 21. Apple and Google need native SDKs behind an AuthProvider
 * port that does not exist yet, so they show a "not available yet" message for now.
 */
export default function SignInScreen() {
  const { t } = useTranslation();
  const [pending, setPending] = useState<Provider | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const social = (provider: Provider) => {
    setPending(provider);
    setMessage(null);
    // TODO(auth): call POST /v1/auth/{provider} with the device id token once the native SDK is wired.
    setPending(null);
    setMessage(t('auth.signIn.socialUnavailable'));
  };

  return (
    <Screen
      footer={
        <>
          <Button
            label={t('auth.signIn.apple')}
            action="secondary"
            icon={<Icon name="logo-apple" color={colors.primary} />}
            loading={pending === 'apple'}
            disabled={pending !== null}
            onPress={() => social('apple')}
          />
          <Button
            label={t('auth.signIn.google')}
            action="secondary"
            icon={<Icon name="logo-google" color={colors.primary} />}
            loading={pending === 'google'}
            disabled={pending !== null}
            onPress={() => social('google')}
          />
          <Button
            label={t('auth.signIn.email')}
            icon={<Icon name="mail-outline" color={colors.onPrimary} />}
            disabled={pending !== null}
            onPress={() => router.push('/(onboarding)/email')}
          />
        </>
      }
    >
      <View className="items-center gap-lg">
        <Logo />
        <Pet mood="happy" name={t('pet.defaultName')} size={200} />
        <Text variant="title" className="text-center">
          {t('auth.signIn.title')}
        </Text>
        <Text variant="secondary" className="text-center">
          {t('auth.signIn.subtitle')}
        </Text>
        {message ? (
          <Text accessibilityRole="alert" className="text-center font-semibold">
            {message}
          </Text>
        ) : null}
      </View>
    </Screen>
  );
}
