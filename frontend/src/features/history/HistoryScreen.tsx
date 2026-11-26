import { router } from 'expo-router';
import { useState } from 'react';
import { FlatList, Pressable, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { useMeals } from '@/api/queries';
import type { MealRange } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { MealCard } from '@/components/MealCard';
import { OfflineBanner } from '@/components/OfflineBanner';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useStartMealLog } from '@/features/meal/useStartMealLog';

import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

import { UndoSnackbar } from './UndoSnackbar';
import { usePendingDeleteStore } from './pendingDelete';

const RANGES: MealRange[] = ['today', '7d', '30d'];

/** Screen 7, empty state 14, and 42 ("Refeição apagada" + Desfazer for 5 s). */
export default function HistoryScreen() {
  const { t } = useTranslation();
  const [range, setRange] = useState<MealRange>('today');
  const meals = useMeals(range);
  const { start } = useStartMealLog();
  const pendingId = usePendingDeleteStore((state) => state.pendingId);
  const items = (meals.data?.pages.flatMap((page) => page.items) ?? []).filter(
    (meal) => meal.id !== pendingId,
  );

  return (
    <SafeAreaView className="flex-1 bg-background" edges={['top', 'left', 'right']}>
      <OfflineBanner />
      <View className="gap-md px-lg pt-xl">
        <Text variant="title">{t('history.title')}</Text>
        <View accessibilityRole="tablist" className="flex-row gap-sm">
          {RANGES.map((option) => {
            const selected = option === range;
            const label = t(`history.ranges.${option}`);
            return (
              <Pressable
                key={option}
                testID={`range-${option}`}
                accessibilityRole="tab"
                accessibilityLabel={label}
                accessibilityState={{ selected }}
                onPress={() => setRange(option)}
                className={cn(
                  'min-h-touch flex-1 flex-row items-center justify-center gap-xs rounded-pill border-2 px-md',
                  selected ? 'border-primary bg-primary' : 'border-input-border bg-surface',
                )}
              >
                {selected ? <Icon name="checkmark" size={18} color={colors.onPrimary} /> : null}
                <Text className={selected ? 'font-heading text-on-primary' : 'font-semibold'}>{label}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {meals.isPending ? (
        <View className="px-lg py-lg">
          <Skeleton lines={4} />
        </View>
      ) : meals.isError ? (
        <View className="px-lg">
          <ErrorState error={meals.error} onRetry={() => void meals.refetch()} />
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(meal) => meal.id}
          renderItem={({ item }) => (
            <MealCard meal={item} onPress={() => router.push(`/meals/${item.id}`)} />
          )}
          contentContainerClassName="grow gap-md px-lg py-lg"
          refreshing={meals.isRefetching}
          onRefresh={() => void meals.refetch()}
          ListEmptyComponent={
            <View testID="history-empty" className="items-center gap-md py-xl">
              <Icon name="restaurant-outline" size={40} color={colors.textSecondary} />
              <Text variant="subtitle" className="text-center">
                {t('history.emptyTitle')}
              </Text>
              <Text variant="secondary" className="text-center">
                {t('history.empty')}
              </Text>
              <Button label={t('history.emptyCta')} onPress={() => void start()} />
            </View>
          }
          ListFooterComponent={
            meals.hasNextPage ? (
              <Button
                action="ghost"
                label={t('history.loadMore')}
                loading={meals.isFetchingNextPage}
                onPress={() => void meals.fetchNextPage()}
              />
            ) : undefined
          }
        />
      )}
      <UndoSnackbar />
    </SafeAreaView>
  );
}
