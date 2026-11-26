import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { Share, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { api } from '@/api/endpoints';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { isApiError, NETWORK_ERROR } from '@/api/client';
import { colors } from '@/theme/tokens';

const CONTENT_KEYS = ['account', 'meals', 'pet', 'subscription'] as const;

/**
 * Screen 36: ready, preparing, done. GET /me/export answers right away (always free, no consent needed),
 * so the file is handed to the system share sheet instead of being "sent by email".
 * The export is never logged or cached.
 */
export default function ExportDataScreen() {
  const { t } = useTranslation();
  const exportData = useMutation({
    mutationFn: async () => {
      const data = await api.exportData();
      await Share.share({ title: t('account.export.shareTitle'), message: JSON.stringify(data, null, 2) });
    },
  });

  return (
    <Screen
      footer={
        <Button
          testID="export-action"
          label={
            exportData.isPending
              ? t('account.export.preparing')
              : exportData.isSuccess
                ? t('account.export.again')
                : t('account.export.action')
          }
          loading={exportData.isPending}
          onPress={() => exportData.mutate()}
        />
      }
    >
      <View className="flex-row items-center gap-sm">
        <IconButton icon="chevron-back" accessibilityLabel={t('common.back')} onPress={() => router.back()} />
        <Text variant="title" className="flex-1">
          {t('account.export.title')}
        </Text>
      </View>
      <Text>{t('account.export.body')}</Text>
      <View className="gap-sm rounded-lg bg-surface p-lg">
        <Text variant="caption">{t('account.export.contents')}</Text>
        {CONTENT_KEYS.map((key) => (
          <View key={key} className="min-h-touch flex-row items-center gap-sm">
            <Icon name="checkmark-circle-outline" color={colors.primary} />
            <Text className="flex-1">{t(`account.export.${key}`)}</Text>
          </View>
        ))}
      </View>
      <Text variant="secondary">{t('account.export.noPhotos')}</Text>
      <Text variant="secondary">{t('account.export.free')}</Text>
      {exportData.isPending ? (
        <Text accessibilityLiveRegion="polite" variant="secondary">
          {t('account.export.preparing')}
        </Text>
      ) : null}
      {exportData.isSuccess ? (
        <Text testID="export-ready" accessibilityLiveRegion="polite" className="font-semibold">
          {t('account.export.ready')}
        </Text>
      ) : null}
      {exportData.isError ? (
        isApiError(exportData.error) && exportData.error.code === NETWORK_ERROR ? (
          <ErrorState error={exportData.error} onRetry={() => exportData.mutate()} />
        ) : (
          <Text testID="export-failed" accessibilityRole="alert" className="font-semibold">
            {t('account.export.failed')}
          </Text>
        )
      ) : null}
    </Screen>
  );
}
