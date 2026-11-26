import { router } from 'expo-router';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { usePet } from '@/api/queries';
import { Hearts } from '@/components/Hearts';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon, type IconName } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

/**
 * Screen 30. Explanatory copy only: the numbers come from docs/domain/pet-rules.md and live in
 * pt-BR.json; the app does not apply these rules itself.
 */
export default function HowLivesWorkScreen() {
  const { t } = useTranslation();
  const pet = usePet();
  const name = pet.data?.name ?? t("pet.defaultName");

  const rows: { icon: IconName; text: string }[] = [
    { icon: 'heart-outline', text: t('onboarding.lives.start', { name }) },
    { icon: 'calendar-outline', text: t('onboarding.lives.loss') },
    { icon: 'trending-up-outline', text: t('onboarding.lives.gain') },
    { icon: 'moon-outline', text: t('onboarding.lives.faint', { name }) },
    { icon: 'camera-outline', text: t('onboarding.lives.limit') },
  ];

  return (
    <Screen
      footer={
        <Button
          testID="lives-start"
          label={t('onboarding.lives.start_cta')}
          onPress={() => router.replace('/(tabs)/home')}
        />
      }
    >
      <Text variant="title">{t('onboarding.lives.title')}</Text>
      {pet.data ? <Hearts lives={pet.data.lives} max={pet.data.max_lives} /> : null}
      <View className="gap-md">
        {rows.map((row) => (
          <View key={row.text} className="flex-row items-start gap-md">
            <Icon name={row.icon} color={colors.primary} />
            <Text className="flex-1">{row.text}</Text>
          </View>
        ))}
      </View>
    </Screen>
  );
}
