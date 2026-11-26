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

const FOOD_GROUPS = ['vegetables', 'protein', 'grains', 'legumes', 'fruits', 'dairy'] as const;

/** Reading confidence in words (the 0..1 number is never shown). */
export function confidenceLevel(confidence: number): 'high' | 'medium' | 'low' {
  if (confidence >= 0.8) return 'high';
  return confidence >= LOW_CONFIDENCE ? 'medium' : 'low';
}

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
            {meal.description ? <Text>{meal.description}</Text> : null}
            {meal.source !== 'manual' && meal.confidence < LOW_CONFIDENCE ? (
              <View className="flex-row items-start gap-sm rounded-md bg-points-bg p-md">
                <Icon name="information-circle-outline" color={colors.pointsText} />
                <Text className="flex-1 text-points-text">{t('meal.result.lowConfidence')}</Text>
              </View>
            ) : null}
            <Text variant="subtitle">{t('meal.result.items')}</Text>
            {meal.items.map((item) => (
              <Text key={item}>• {item}</Text>
            ))}
            {meal.source === 'manual' ? null : (
              <View testID="about-free" className="gap-sm">
                <View className="flex-row items-center justify-between gap-sm">
                  <Text variant="caption">{t('meal.result.groupsTitle')}</Text>
                  <Text variant="caption" className="rounded-pill bg-points-bg px-sm py-xs text-points-text">
                    {t('meal.result.free')}
                  </Text>
                </View>
                {FOOD_GROUPS.map((group) => {
                  const present = meal.food_groups.includes(group);
                  return (
                    <View
                      key={group}
                      testID={`group-${group}`}
                      accessible
                      accessibilityLabel={`${foodGroupLabel(group)}, ${
                        present ? t('meal.result.groupPresent') : t('meal.result.groupAbsent')
                      }`}
                      className="min-h-touch flex-row items-center gap-sm rounded-md bg-background px-md"
                    >
                      <Icon
                        name={present ? 'checkmark-circle' : 'remove-circle-outline'}
                        color={present ? colors.primary : colors.textSecondary}
                      />
                      <Text className={present ? 'flex-1 font-semibold' : 'flex-1 text-ink-secondary'}>
                        {foodGroupLabel(group)}
                      </Text>
                      <Text variant="caption">
                        {present ? t('meal.result.groupPresent') : t('meal.result.groupAbsent')}
                      </Text>
                    </View>
                  );
                })}
                <Text testID="about-counts">
                  {t('meal.detail.itemCount', { count: meal.item_count })} ·{' '}
                  {t('meal.detail.colorCount', { count: meal.colors.length })}
                </Text>
                <Text testID="about-confidence">
                  {t('meal.result.confidence', { level: t(`meal.result.confidenceLevel.${confidenceLevel(meal.confidence)}`) })}
                </Text>
              </View>
            )}
          </View>
        ) : null}
      </View>

      <View testID="habits-locked" className="gap-sm rounded-lg bg-surface p-lg">
        <View
          testID="habits-locked-label"
          accessible
          accessibilityLabel={t('meal.result.habitsLocked')}
          accessibilityState={{ disabled: true }}
          className="min-h-touch flex-row items-center gap-sm"
        >
          <Icon name="lock-closed-outline" color={colors.textSecondary} />
          <Text variant="subtitle" className="flex-1">
            {t('meal.result.habits')}
          </Text>
          <Text variant="caption" className="rounded-pill bg-points-bg px-sm py-xs text-points-text">
            {t('profile.premiumTag')}
          </Text>
        </View>
        <View
          testID="habits-blurred"
          accessibilityElementsHidden
          importantForAccessibility="no-hide-descendants"
          className="gap-xs opacity-30"
        >
          {[0.8, 0.55, 0.4].map((width) => (
            <View key={width} className="min-h-[14px] rounded-pill bg-ink-secondary" style={{ width: `${width * 100}%` }} />
          ))}
        </View>
        <Button
          testID="habits-unlock"
          action="secondary"
          label={t('meal.result.unlock')}
          icon={<Icon name="lock-open-outline" color={colors.primary} />}
          onPress={() => router.push('/premium')}
        />
      </View>
    </Screen>
  );
}
