import { Redirect, router } from 'expo-router';
import { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Hearts } from '@/components/Hearts';
import { Pet } from '@/components/Pet';
import { PointsBadge } from '@/components/PointsBadge';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useMealFlowStore } from '@/stores/mealFlow';
import { colors } from '@/theme/tokens';

import { LOW_CONFIDENCE } from './analysisOutcome';
import { foodGroupLabel } from './labels';
import { shouldAskForNotifications } from './notificationsPrompt';

/** Screen 6: "Sobre este prato" open by default; pet reacts to the events from the API. */
export default function ResultScreen() {
  const { t } = useTranslation();
  const result = useMealFlowStore((state) => state.result);
  const [open, setOpen] = useState(true);

  if (!result) return <Redirect href="/(tabs)/home" />;
  const { meal, pet, events } = result;
  const name = pet.name ?? t('pet.defaultName');

  const done = async () => {
    const askNotifications = await shouldAskForNotifications();
    router.replace(askNotifications ? '/meal/notifications' : '/(tabs)/home');
  };

  return (
    <Screen footer={<Button testID="result-done" label={t('meal.result.done')} onPress={() => void done()} />}>
      <Text variant="title" className="text-center">
        {t('meal.result.title')}
      </Text>
      <Pet mood={pet.mood} events={events} name={name} size={180} className="self-center" />
      <View className="flex-row flex-wrap items-center justify-center gap-md">
        <Hearts lives={pet.lives} max={pet.max_lives} />
        <PointsBadge points={pet.points} />
      </View>

      <View className="rounded-lg bg-surface">
        <Pressable
          testID="about-toggle"
          accessibilityRole="button"
          accessibilityLabel={t('meal.result.about')}
          accessibilityState={{ expanded: open }}
          onPress={() => setOpen((value) => !value)}
          className="min-h-touch flex-row items-center justify-between px-lg py-md"
        >
          <Text variant="subtitle">{t('meal.result.about')}</Text>
          <Icon name={open ? 'chevron-up' : 'chevron-down'} color={colors.text} />
        </Pressable>
        {open ? (
          <View testID="about-content" className="gap-md px-lg pb-lg">
            <Text variant="caption">{t(`meal.types.${meal.meal_type}`)}</Text>
            <Text>{meal.description}</Text>
            {meal.confidence < LOW_CONFIDENCE ? (
              <View className="flex-row items-start gap-sm rounded-md bg-points-bg p-md">
                <Icon name="information-circle-outline" color={colors.pointsText} />
                <Text className="flex-1 text-points-text">{t('meal.result.lowConfidence')}</Text>
              </View>
            ) : null}
            <Text variant="subtitle">{t('meal.result.items')}</Text>
            {meal.items.map((item) => (
              <Text key={item}>• {item}</Text>
            ))}
            {meal.food_groups.length ? (
              <>
                <Text variant="subtitle">{t('meal.result.groups')}</Text>
                <Text>{meal.food_groups.map(foodGroupLabel).join(', ')}</Text>
              </>
            ) : null}
          </View>
        ) : null}
      </View>

      <View
        accessible
        accessibilityLabel={t('meal.result.habitsLocked')}
        accessibilityState={{ disabled: true }}
        className="min-h-touch flex-row items-center gap-sm rounded-lg bg-surface px-lg py-md"
      >
        <Icon name="lock-closed-outline" color={colors.textSecondary} />
        <Text variant="secondary" className="flex-1">
          {t('meal.result.habits')}
        </Text>
      </View>
    </Screen>
  );
}
