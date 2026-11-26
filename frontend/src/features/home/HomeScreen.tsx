import { Redirect, useFocusEffect } from 'expo-router';
import { useCallback } from 'react';
import { RefreshControl, ScrollView, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { usePet } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Hearts } from '@/components/Hearts';
import { OfflineBanner } from '@/components/OfflineBanner';
import { Pet, haloFor } from '@/components/Pet';
import { PointsBadge } from '@/components/PointsBadge';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useStartMealLog } from '@/features/meal/useStartMealLog';
import { colors } from '@/theme/tokens';

/** Screen 3 (and 40 when the photos are used up). Renders mood, lives and events from GET /pet. */
export default function HomeScreen() {
  const { t } = useTranslation();
  const pet = usePet();
  const { start, limitReached } = useStartMealLog();

  // GET /pet settles lives; refresh whenever Home comes back into view.
  useFocusEffect(
    useCallback(() => {
      void pet.refetch();
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []),
  );

  let content;
  if (pet.isPending) {
    content = <Skeleton hero lines={2} />;
  } else if (pet.isError) {
    content = <ErrorState error={pet.error} onRetry={() => void pet.refetch()} />;
  } else {
    const data = pet.data;
    // Screen 43: the pet stays hidden until it has a name.
    if (data.name === null) return <Redirect href="/(onboarding)/name-pet" />;
    const name = data.name;
    const firstDay = data.streak_days === 0 && data.points === 0;
    content = (
      <>
        <View className="flex-row flex-wrap items-center justify-between gap-sm">
          <Hearts lives={data.lives} max={data.max_lives} />
          <PointsBadge points={data.points} />
        </View>
        <View
          className="items-center self-center rounded-pill p-lg"
          style={{ backgroundColor: haloFor(data.color) }}
        >
          <Pet mood={data.mood} events={data.events} name={name} />
        </View>
        <Text variant="title" className="text-center">
          {name}
        </Text>
        <Text testID="mood-message" className="text-center">
          {firstDay ? t('home.firstDay') : t(`home.moodMessage.${data.mood}`, { name })}
        </Text>
        {data.streak_days > 0 ? (
          <View className="flex-row items-center justify-center gap-xs">
            <Icon name="flame-outline" color={colors.primary} />
            <Text variant="secondary">{t('home.streak', { count: data.streak_days })}</Text>
          </View>
        ) : null}
        {limitReached ? (
          <Text testID="photos-used-up" variant="secondary" className="text-center">
            {t('home.photosUsedUp')}
          </Text>
        ) : null}
      </>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-background" edges={['top', 'left', 'right']}>
      <OfflineBanner />
      <ScrollView
        contentContainerClassName="grow gap-lg px-lg py-xl"
        refreshControl={
          <RefreshControl refreshing={pet.isRefetching} onRefresh={() => void pet.refetch()} />
        }
      >
        {content}
      </ScrollView>
      {pet.isSuccess ? (
        <View className="px-lg pb-lg pt-sm">
          <Button
            testID="log-meal"
            label={t('home.logMeal')}
            icon={<Icon name="camera" color={colors.onPrimary} />}
            onPress={() => void start()}
          />
        </View>
      ) : null}
    </SafeAreaView>
  );
}
