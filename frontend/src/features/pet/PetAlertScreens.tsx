import { router } from 'expo-router';
import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { usePet } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Pet } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { useStartMealLog } from '@/features/meal/useStartMealLog';
import { colors } from '@/theme/tokens';

type Kind = 'lifeLost' | 'fainted';

/**
 * Screens 28 (lost a life) and 12 (fainted). Everything shown comes from GET /pet:
 * the app never decides that a life was lost. "Pause" opens the Premium placeholder (Phase 2).
 */
function PetAlert({ kind }: { kind: Kind }) {
  const { t } = useTranslation();
  const pet = usePet();
  const { start } = useStartMealLog();

  const close = () => router.replace('/(tabs)/home');
  const log = () => {
    close();
    void start();
  };

  if (pet.isPending) {
    return (
      <Screen>
        <Skeleton hero lines={2} />
      </Screen>
    );
  }
  if (pet.isError) {
    return (
      <Screen footer={<Button action="ghost" label={t('common.close')} onPress={close} />}>
        <ErrorState error={pet.error} onRetry={() => void pet.refetch()} />
      </Screen>
    );
  }

  const data = pet.data;
  const name = data.name ?? t('pet.defaultName');
  const copy = `petAlert.${kind}` as const;

  return (
    <Screen
      footer={
        <>
          <Button
            testID="alert-log"
            label={t(`${copy}.cta`)}
            icon={<Icon name="camera" color={colors.onPrimary} />}
            onPress={log}
          />
          <Pressable
            testID="alert-pause"
            accessibilityRole="button"
            accessibilityLabel={`${t(`${copy}.pause`)}, ${t('petAlert.premiumTag')}`}
            onPress={() => router.push('/premium')}
            className="min-h-touch flex-row flex-wrap items-center justify-center gap-sm"
          >
            <Text className="font-heading text-primary">{t(`${copy}.pause`)}</Text>
            <Text
              variant="caption"
              className="rounded-pill bg-points-bg px-sm py-xs text-points-text"
            >
              {t('petAlert.premiumTag')}
            </Text>
          </Pressable>
          <Button action="ghost" label={t(`${copy}.close`)} onPress={close} />
        </>
      }
    >
      <View className="flex-1 items-center justify-center gap-lg">
        {kind === 'fainted' ? (
          <Text
            variant="caption"
            className="rounded-pill bg-points-bg px-md py-xs text-points-text"
          >
            {t('petAlert.fainted.badge')}
          </Text>
        ) : null}
        <Pet mood={data.mood} name={name} size={170} />
        <Text variant="title" className="text-center">
          {t(`${copy}.title`, { name })}
        </Text>
        <Text variant="secondary" className="text-center">
          {kind === 'lifeLost'
            ? t('petAlert.lifeLost.body', { count: data.lives, name })
            : t('petAlert.fainted.body')}
        </Text>
      </View>
    </Screen>
  );
}

export const LifeLostScreen = () => <PetAlert kind="lifeLost" />;
export const FaintedScreen = () => <PetAlert kind="fainted" />;
