import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import type { Meal } from '@/api/types';
import { Text } from '@/components/ui/Text';
import { formatMealTime } from '@/utils/date';

/** History row: meal type, time and description. No scores or health labels, ever. */
export function MealCard({ meal }: { meal: Meal }) {
  const { t } = useTranslation();
  const type = t(`meal.types.${meal.meal_type}`);
  const time = formatMealTime(meal.logged_at);
  return (
    <View
      testID="meal-card"
      accessible
      accessibilityLabel={`${type}, ${time}. ${meal.description}`}
      className="gap-xs rounded-lg bg-surface p-lg"
    >
      <View className="flex-row flex-wrap items-center justify-between gap-sm">
        <Text variant="subtitle">{type}</Text>
        <Text variant="caption">{time}</Text>
      </View>
      <Text variant="secondary">{meal.description}</Text>
    </View>
  );
}
