import { router } from 'expo-router';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Screen } from '@/components/Screen';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

import { SupportPath } from './SupportPath';

/** Profile > Apoio: the app does not replace a doctor or nutritionist; a kind path to CVV 188. */
export default function SupportScreen() {
  const { t } = useTranslation();
  return (
    <Screen>
      <View className="flex-row items-center gap-sm">
        <IconButton icon="chevron-back" accessibilityLabel={t('common.back')} onPress={() => router.back()} />
        <Text variant="title" className="flex-1">
          {t('support.title')}
        </Text>
      </View>
      <View className="flex-row items-start gap-sm rounded-lg bg-surface p-lg">
        <Icon name="information-circle-outline" color={colors.primary} />
        <Text testID="support-notice" className="flex-1">
          {t('support.notice')}
        </Text>
      </View>
      <Text variant="subtitle">{t('support.pathTitle')}</Text>
      <Text>{t('support.pathBody')}</Text>
      <SupportPath />
    </Screen>
  );
}
