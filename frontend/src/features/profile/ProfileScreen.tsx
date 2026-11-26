import { useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { useMe } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Icon, type IconName } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useNotificationsSummary } from '@/features/account/useNotificationSettings';
import { endSession } from '@/features/auth/session';
import { colors } from '@/theme/tokens';

interface RowProps {
  testID?: string;
  icon: IconName;
  label: string;
  /** Text shown on the right (a value or a tag). */
  trailing?: ReactNode;
  onPress: () => void;
  /** Spoken label; defaults to the visible label. */
  accessibilityLabel?: string;
}

function Row({ testID, icon, label, trailing, onPress, accessibilityLabel }: RowProps) {
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      onPress={onPress}
      className="min-h-touch flex-row items-center gap-md border-b border-background px-lg py-sm"
    >
      <Icon name={icon} color={colors.text} />
      <Text className="flex-1 font-semibold">{label}</Text>
      {trailing}
    </Pressable>
  );
}

/** "São Paulo" from "America/Sao_Paulo": display only. */
const cityOf = (timezone: string) => timezone.split('/').pop()?.replace(/_/g, ' ') ?? timezone;

/** Screen 8. Entry to notifications (27), export (36), delete account (35). */
export default function ProfileScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const me = useMe();
  const notificationsOn = useNotificationsSummary();

  const signOut = async () => {
    await endSession(queryClient);
    router.replace('/(onboarding)/sign-in');
  };

  return (
    <Screen
      footer={
        <Pressable
          testID="delete-account-link"
          accessibilityRole="button"
          accessibilityLabel={t('profile.deleteAccount')}
          onPress={() => router.push('/account/delete')}
          className="min-h-touch items-center justify-center"
        >
          <Text className="font-heading text-danger">{t('profile.deleteAccount')}</Text>
        </Pressable>
      }
    >
      <Text variant="title">{t('profile.title')}</Text>
      {me.isPending ? (
        <Skeleton lines={4} />
      ) : me.isError ? (
        <ErrorState error={me.error} onRetry={() => void me.refetch()} />
      ) : (
        <>
          <View className="flex-row items-center gap-lg">
            <View
              accessible
              accessibilityRole="image"
              accessibilityLabel={t('profile.avatarLabel', { name: me.data.name })}
              className="h-16 w-16 items-center justify-center rounded-pill bg-points-bg"
            >
              <Text variant="title" className="text-points-text">
                {me.data.name.trim().charAt(0).toUpperCase()}
              </Text>
            </View>
            <View className="flex-1">
              <Text variant="subtitle">{me.data.name}</Text>
              <Text variant="secondary">{me.data.email}</Text>
            </View>
          </View>

          {me.data.plan === 'free' ? (
            <Pressable
              testID="premium-banner"
              accessibilityRole="button"
              accessibilityLabel={`${t('profile.premiumTitle')}. ${t('profile.premiumBody')}`}
              onPress={() => router.push('/premium')}
              className="min-h-touch flex-row items-center gap-md rounded-lg bg-primary p-lg"
            >
              <View className="flex-1">
                <Text className="font-heading text-on-primary">{t('profile.premiumTitle')}</Text>
                <Text className="text-on-primary">{t('profile.premiumBody')}</Text>
              </View>
              <Icon name="chevron-forward" color={colors.onPrimary} />
            </Pressable>
          ) : (
            <Text
              variant="caption"
              className="self-start rounded-pill bg-points-bg px-md py-xs text-points-text"
            >
              {t(`profile.plan.${me.data.plan}`)}
            </Text>
          )}

          <View className="overflow-hidden rounded-lg bg-surface">
            <Row
              testID="row-notifications"
              icon="notifications-outline"
              label={t('profile.notifications')}
              accessibilityLabel={`${t('profile.notifications')}, ${
                notificationsOn ? t('profile.notificationsOn') : t('profile.notificationsOff')
              }`}
              onPress={() => router.push('/account/notifications')}
              trailing={
                <Text variant="secondary">
                  {notificationsOn ? t('profile.notificationsOn') : t('profile.notificationsOff')}
                </Text>
              }
            />
            <Row
              testID="row-pause"
              icon="pause-outline"
              label={t('profile.pause')}
              accessibilityLabel={`${t('profile.pause')}, ${t('profile.premiumTag')}`}
              onPress={() => router.push('/premium')}
              trailing={
                <Text
                  variant="caption"
                  className="rounded-pill bg-points-bg px-sm py-xs text-points-text"
                >
                  {t('profile.premiumTag')}
                </Text>
              }
            />
            <View
              testID="row-timezone"
              accessible
              accessibilityLabel={`${t('profile.timezone')}, ${cityOf(me.data.timezone)}`}
              className="min-h-touch flex-row items-center gap-md px-lg py-sm"
            >
              <Icon name="globe-outline" color={colors.text} />
              <Text className="flex-1 font-semibold">{t('profile.timezone')}</Text>
              <Text variant="secondary">{cityOf(me.data.timezone)}</Text>
            </View>
          </View>

          <View className="overflow-hidden rounded-lg bg-surface">
            <Row
              testID="row-export"
              icon="download-outline"
              label={t('profile.export')}
              onPress={() => router.push('/account/export')}
            />
            <Row
              testID="row-sign-out"
              icon="log-out-outline"
              label={t('profile.signOut')}
              onPress={() => void signOut()}
            />
          </View>
        </>
      )}
    </Screen>
  );
}
