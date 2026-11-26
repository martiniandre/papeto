import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

/** Premium is Phase 2: this placeholder is where "Pause" (13/15) will open. No prices, no purchase. */
export default function PremiumPlaceholderScreen() {
  const { t } = useTranslation();
  return (
    <Screen
      footer={<Button testID="premium-close" label={t('premium.close')} onPress={() => router.back()} />}
    >
      <Icon name="moon-outline" size={48} color={colors.primary} />
      <Text variant="title">{t('premium.title')}</Text>
      <Text>{t('premium.body')}</Text>
      <Text variant="secondary">{t('premium.soon')}</Text>
    </Screen>
  );
}
