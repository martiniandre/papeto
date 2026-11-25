import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { usePet } from '@/api/queries';
import { Pet } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';

/** Screen 11: 2 of 2 photos used; resets at local midnight; never costs a life. */
export default function DailyLimitScreen() {
  const { t } = useTranslation();
  const pet = usePet();

  return (
    <Screen
      footer={<Button label={t('meal.limit.home')} onPress={() => router.replace('/(tabs)/home')} />}
    >
      {pet.data ? (
        <Pet
          mood={pet.data.mood}
          name={pet.data.name}
          size={160}
          className="self-center"
        />
      ) : null}
      <Text variant="title">{t('meal.limit.title')}</Text>
      <Text>{t('meal.limit.body')}</Text>
      <Text>{t('meal.limit.reset')}</Text>
      <Text variant="secondary">{t('meal.limit.lives')}</Text>
    </Screen>
  );
}
