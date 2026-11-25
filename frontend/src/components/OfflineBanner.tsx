import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useOnline } from '@/hooks/useOnline';
import { colors } from '@/theme/tokens';

/** "Sem conexão" banner shown on every screen while the device is offline. */
export function OfflineBanner() {
  const { t } = useTranslation();
  const online = useOnline();
  if (online) return null;
  return (
    <View
      testID="offline-banner"
      accessible
      accessibilityRole="alert"
      accessibilityLiveRegion="polite"
      className="flex-row items-center gap-sm bg-ink px-lg py-sm"
    >
      <Icon name="cloud-offline-outline" size={20} color={colors.onPrimary} />
      <Text className="flex-1 text-on-primary">{t('common.offline')}</Text>
    </View>
  );
}
