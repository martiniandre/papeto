import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import type { Meal } from '@/api/types';
import { Text } from '@/components/ui/Text';
import { formatMealTime } from '@/utils/date';

/** History row: meal type, time and description. No scores or health labels, ever. */
export function MealCard({ meal, onPress }: { meal: Meal; onPress?: () => void }) {
  const { t } = useTranslation();
  const type = t(`meal.types.${meal.meal_type}`);
  const time = formatMealTime(meal.logged_at);
  const body = (
    <>
      <View className="flex-row flex-wrap items-center justify-between gap-sm">
        <Text variant="subtitle">{type}</Text>
        <Text variant="caption">{time}</Text>
      </View>
      <Text variant="secondary">{meal.description}</Text>
    </>
  );
  const label = `${type}, ${time}. ${meal.description}`;
  if (!onPress) {
    return (
      <View testID="meal-card" accessible accessibilityLabel={label} className="gap-xs rounded-lg bg-surface p-lg">
        {body}
      </View>
    );
  }
  return (
    <Pressable
      testID="meal-card"
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityHint={t('history.openMeal')}
      onPress={onPress}
      className="min-h-touch gap-xs rounded-lg bg-surface p-lg"
    >
      {body}
    </Pressable>
  );
}
