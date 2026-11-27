import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { Logo } from '@/components/Logo';
import { Pet } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { errorMessage } from '@/i18n';
import { colors } from '@/theme/tokens';

import { useAuthActions } from './useAuthActions';
import { GoogleSignInError, useGoogleSignIn } from './useGoogleSignIn';

/**
 * Screen 1. Google (id token → POST /v1/auth/google) or e-mail (21). Apple is hidden for now
 * (product decision 2026-11-26). Each backend error code has its own message.
 */
export default function SignInScreen() {
  const { t } = useTranslation();
  const google = useGoogleSignIn();
  const { signInWithGoogle } = useAuthActions();
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const onGoogle = async () => {
    setMessage(null);
    if (!google.available) {
      setMessage(t('auth.signIn.googleUnavailable'));
      return;
    }
    setPending(true);
    try {
      await signInWithGoogle(await google.signIn());
    } catch (error) {
      if (error instanceof GoogleSignInError) {
        if (error.reason === 'unavailable') setMessage(t('auth.signIn.googleUnavailable'));
        else if (error.reason === 'failed') setMessage(t('auth.signIn.googleFailed'));
        // 'cancelled': the user closed the picker; no message.
      } else if (isApiError(error)) {
        setMessage(errorMessage(error.code));
      } else {
        setMessage(t('auth.signIn.googleFailed'));
      }
    } finally {
      setPending(false);
    }
  };

  return (
    <Screen
      footer={
        <>
          <Button
            label={t('auth.signIn.google')}
            action="secondary"
            icon={<Icon name="logo-google" color={colors.primary} />}
            accessibilityLabel={t('auth.signIn.google')}
            testID="google-sign-in"
            loading={pending}
            disabled={pending}
            onPress={() => void onGoogle()}
          />
          <Button
            label={t('auth.signIn.email')}
            icon={<Icon name="mail-outline" color={colors.onPrimary} />}
            disabled={pending}
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
        {pending ? (
          <Text accessibilityLiveRegion="polite" variant="secondary" className="text-center">
            {t('auth.signIn.googleProgress')}
          </Text>
        ) : null}
        {message ? (
          <Text accessibilityRole="alert" className="text-center font-semibold">
            {message}
          </Text>
        ) : null}
      </View>
    </Screen>
  );
}
