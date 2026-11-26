import { router } from 'expo-router';
import { Image, Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { PET_COLORS, type PetColor } from '@/api/types';
import { usePet, useUpdatePet } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { frontArt, haloFor } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

/** Screen 24: reveal with the chosen name and pick a color. */
export default function MeetPetScreen() {
  const { t } = useTranslation();
  const pet = usePet();
  const updatePet = useUpdatePet();

  if (pet.isPending) {
    return (
      <Screen>
        <Skeleton hero />
      </Screen>
    );
  }
  if (pet.isError) {
    return (
      <Screen>
        <ErrorState error={pet.error} onRetry={() => void pet.refetch()} />
      </Screen>
    );
  }

  const name = pet.data.name ?? t('pet.defaultName');
  const color: PetColor = updatePet.variables?.color ?? pet.data.color;

  return (
    <Screen
      footer={
        <Button
          testID="meet-continue"
          label={t('common.continue')}
          loading={updatePet.isPending}
          onPress={() => router.replace('/(onboarding)/how-lives-work')}
        />
      }
    >
      <Text variant="title" className="text-center">
        {t('onboarding.meet.title', { name })}
      </Text>
      <View
        className="items-center self-center rounded-pill p-lg"
        style={{ backgroundColor: haloFor(color) }}
      >
        <Image
          source={frontArt}
          accessibilityRole="image"
          accessibilityLabel={name}
          resizeMode="contain"
          style={{ width: 220, height: 220 }}
        />
      </View>
      <Text variant="subtitle">{t('onboarding.meet.body')}</Text>
      <View accessibilityRole="radiogroup" className="flex-row flex-wrap justify-center gap-md">
        {PET_COLORS.map((option) => {
          const selected = option === color;
          const colorName = t(`onboarding.meet.colors.${option}`);
          return (
            <Pressable
              key={option}
              testID={`color-${option}`}
              accessibilityRole="radio"
              accessibilityLabel={t('onboarding.meet.colorLabel', { color: colorName })}
              accessibilityState={{ selected, checked: selected }}
              onPress={() => updatePet.mutate({ color: option })}
              className={
                selected
                  ? 'min-h-touch min-w-touch items-center justify-center rounded-pill border-4 border-primary'
                  : 'min-h-touch min-w-touch items-center justify-center rounded-pill border-2 border-input-border'
              }
              style={{ backgroundColor: haloFor(option), width: 56, height: 56 }}
            >
              {selected ? <Icon name="checkmark" size={24} color={colors.primary} /> : null}
            </Pressable>
          );
        })}
      </View>
    </Screen>
  );
}
