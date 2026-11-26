import { useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useEffect } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Pet } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { endSession } from '@/features/auth/session';
import { useSessionStore } from '@/stores/session';

/**
 * Screen 41. Ends the local session on arrival (tokens and caches cleared); signing in again within
 * 30 days cancels the deletion.
 */
export default function AccountDeletedScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  useEffect(() => {
    void endSession(queryClient);
  }, [queryClient]);

  return (
    <Screen
      footer={
        <Button
          testID="to-sign-in"
          label={t('account.deleted.toSignIn')}
          onPress={() => {
            useSessionStore.getState().setStatus('signedOut');
            router.replace('/(onboarding)/sign-in');
          }}
        />
      }
    >
      <View accessibilityRole="alert" className="flex-1 items-center justify-center gap-lg">
        <Pet mood="sleepy" name={t('account.deleted.imageLabel')} size={170} />
        <Text variant="title" className="text-center">
          {t('account.deleted.title')}
        </Text>
        <Text variant="secondary" className="text-center">
          {t('account.deleted.body')}
        </Text>
      </View>
    </Screen>
  );
}
