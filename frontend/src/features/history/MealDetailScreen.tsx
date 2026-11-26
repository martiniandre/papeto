import { useQueryClient } from '@tanstack/react-query';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { useMeal } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { foodGroupLabel } from '@/features/meal/labels';
import { colors } from '@/theme/tokens';
import { formatMealTime, isSameLocalDay } from '@/utils/date';

import { DeleteMealSheet } from './DeleteMealSheet';
import { scheduleMealDelete } from './pendingDelete';

/** Screen 25: meal detail. Never shows points, scores or health labels. */
export default function MealDetailScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { id } = useLocalSearchParams<{ id: string }>();
  const meal = useMeal(String(id));
  const [confirming, setConfirming] = useState(false);

  const confirmDelete = () => {
    setConfirming(false);
    scheduleMealDelete(String(id), queryClient);
    // Back to History (screen 42), where "Refeição apagada" + "Desfazer" is shown.
    router.dismissTo('/(tabs)/history');
  };

  const header = (
    <View className="flex-row items-center gap-sm">
      <IconButton
        testID="detail-back"
        icon="chevron-back"
        accessibilityLabel={t('common.back')}
        onPress={() => router.back()}
      />
      <Text variant="title" className="flex-1">
        {meal.data ? t(`meal.types.${meal.data.meal_type}`) : t('meal.detail.title')}
      </Text>
    </View>
  );

  if (meal.isPending) {
    return (
      <Screen>
        {header}
        <Skeleton lines={5} />
      </Screen>
    );
  }
  if (meal.isError) {
    return (
      <Screen>
        {header}
        <ErrorState error={meal.error} onRetry={() => void meal.refetch()} />
      </Screen>
    );
  }

  const data = meal.data;
  const time = formatMealTime(data.logged_at);
  const when = isSameLocalDay(data.logged_at) ? t('meal.detail.today', { time }) : time;
  const counts = [
    t('meal.detail.itemCount', { count: data.items.length }),
    t('meal.detail.colorCount', { count: data.colors.length }),
  ].join(' · ');

  return (
    <Screen
      footer={
        <View className="flex-row gap-md">
          <Button
            testID="detail-edit"
            className="flex-1"
            action="secondary"
            label={t('meal.detail.edit')}
            onPress={() => router.push(`/meals/${String(id)}/edit`)}
          />
          <Button
            testID="detail-delete"
            className="flex-1"
            action="secondary"
            label={t('meal.detail.delete')}
            onPress={() => setConfirming(true)}
          />
        </View>
      }
    >
      {header}
      <View className="flex-row items-center gap-sm">
        <Icon name="information-circle-outline" color={colors.textSecondary} />
        <Text variant="caption" className="flex-1">
          {t('meal.detail.photoDiscarded')}
        </Text>
      </View>
      <View className="gap-md rounded-lg bg-surface p-lg">
        <Text>{data.description}</Text>
        <View className="flex-row flex-wrap gap-sm">
          {data.items.map((item) => (
            <View
              key={item}
              className="min-h-touch justify-center rounded-pill border border-input-border px-md"
            >
              <Text className="font-semibold">{item}</Text>
            </View>
          ))}
        </View>
        {data.food_groups.length ? (
          <>
            <Text variant="subtitle">{t('meal.detail.about')}</Text>
            <Text variant="secondary">{data.food_groups.map(foodGroupLabel).join(', ')}</Text>
          </>
        ) : null}
        <Text variant="caption">{counts}</Text>
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
      <View className="gap-sm rounded-lg bg-surface p-lg">
        <View className="min-h-touch flex-row items-center justify-between gap-md">
          <Text variant="secondary">{t('meal.detail.when')}</Text>
          <Text className="font-semibold">{when}</Text>
        </View>
        <View className="min-h-touch flex-row items-center justify-between gap-md">
          <Text variant="secondary">{t('meal.detail.type')}</Text>
          <Text className="font-semibold">{t(`meal.types.${data.meal_type}`)}</Text>
        </View>
      </View>
      <DeleteMealSheet visible={confirming} onConfirm={confirmDelete} onKeep={() => setConfirming(false)} />
    </Screen>
  );
}
