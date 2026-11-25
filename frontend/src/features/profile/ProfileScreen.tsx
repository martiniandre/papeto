import { useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { useMe } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { endSession } from '@/features/auth/session';

/** Screen 8 (basic). Notifications, export and delete account belong to flow 4. */
export default function ProfileScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const me = useMe();

  const signOut = async () => {
    await endSession(queryClient);
    router.replace('/(onboarding)/sign-in');
  };

  return (
    <Screen footer={<Button action="secondary" label={t('profile.signOut')} onPress={() => void signOut()} />}>
      <Text variant="title">{t('profile.title')}</Text>
      {me.isPending ? (
        <Skeleton lines={3} />
      ) : me.isError ? (
        <ErrorState error={me.error} onRetry={() => void me.refetch()} />
      ) : (
        <View className="gap-md rounded-lg bg-surface p-lg">
          <Text variant="subtitle">{me.data.name}</Text>
          <View>
            <Text variant="caption">{t('profile.email')}</Text>
            <Text>{me.data.email}</Text>
          </View>
          <Text
            variant="caption"
            className="self-start rounded-pill bg-points-bg px-md py-xs text-points-text"
          >
            {t(`profile.plan.${me.data.plan}`)}
          </Text>
        </View>
      )}
    </Screen>
  );
}
