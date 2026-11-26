import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Linking, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { usePet } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { ToggleRow } from '@/components/ui/ToggleRow';
import { colors } from '@/theme/tokens';

import { useNotificationSettings } from './useNotificationSettings';

/** Screen 27: on, off, and "denied by the system" (link to Settings). */
export default function NotificationsSettingsScreen() {
  const { t } = useTranslation();
  const pet = usePet();
  const { settings, isLoading, isError, isSaving, update, retry } = useNotificationSettings();
  const [denied, setDenied] = useState(false);
  const name = pet.data?.name ?? t('pet.defaultName');

  useEffect(() => {
    let active = true;
    Notifications.getPermissionsAsync()
      .then(({ status }) => {
        if (active) setDenied(status === 'denied');
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);

  const header = (
    <View className="flex-row items-center gap-sm">
      <IconButton icon="chevron-back" accessibilityLabel={t('common.back')} onPress={() => router.back()} />
      <Text variant="title" className="flex-1">
        {t('account.notifications.title')}
      </Text>
    </View>
  );

  if (isLoading) {
    return (
      <Screen>
        {header}
        <Skeleton lines={4} />
      </Screen>
    );
  }
  if (isError) {
    return (
      <Screen>
        {header}
        <ErrorState error={new Error('settings')} onRetry={retry} />
      </Screen>
    );
  }

  return (
    <Screen>
      {header}
      {denied ? (
        <View
          testID="notifications-denied"
          accessibilityRole="alert"
          className="gap-sm rounded-lg bg-points-bg p-lg"
        >
          <View className="flex-row items-center gap-sm">
            <Icon name="notifications-off-outline" color={colors.pointsText} />
            <Text className="flex-1 font-heading text-points-text">
              {t('account.notifications.deniedTitle')}
            </Text>
          </View>
          <Text className="text-points-text">{t('account.notifications.deniedBody')}</Text>
          <Button
            action="secondary"
            label={t('common.openSettings')}
            onPress={() => void Linking.openSettings()}
          />
        </View>
      ) : null}

      <View className="gap-sm">
        <Text variant="caption">{t('account.notifications.howTitle')}</Text>
        <View className="gap-xs rounded-lg bg-surface p-lg">
          <Text className="font-heading">{t('account.notifications.example1Title', { name })}</Text>
          <Text variant="secondary">{t('account.notifications.example1Body')}</Text>
        </View>
        <View className="gap-xs rounded-lg bg-surface p-lg">
          <Text className="font-heading">{t('account.notifications.example2Title')}</Text>
          <Text variant="secondary">{t('account.notifications.example2Body', { name })}</Text>
        </View>
      </View>

      <View className="rounded-lg bg-surface px-lg">
        <ToggleRow
          testID="toggle-meal"
          label={t('account.notifications.mealReminder')}
          value={settings.mealReminder}
          disabled={isSaving}
          onChange={(value) => update({ mealReminder: value })}
        />
        <ToggleRow
          testID="toggle-sleepy"
          label={t('account.notifications.sleepy')}
          value={settings.sleepy}
          disabled={isSaving}
          onChange={(value) => update({ sleepy: value })}
        />
        <ToggleRow
          testID="toggle-weekly"
          label={t('account.notifications.weekly')}
          value={settings.weekly}
          disabled={isSaving}
          onChange={(value) => update({ weekly: value })}
        />
        <ToggleRow
          testID="toggle-quiet"
          label={t('account.notifications.quiet')}
          detail={t('account.notifications.quietRange')}
          value={settings.quietHours}
          disabled={isSaving}
          onChange={(value) => update({ quietHours: value })}
        />
      </View>
      <Text variant="secondary">{t('account.notifications.footnote')}</Text>
    </Screen>
  );
}
