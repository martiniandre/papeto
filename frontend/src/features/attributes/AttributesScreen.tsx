import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { usePet, useSpendAttributes } from '@/api/queries';
import {
  ATTRIBUTE_NAMES,
  type AttributeAllocations,
  type AttributeName,
  type Pet,
} from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { errorMessage } from '@/i18n';
import { colors } from '@/theme/tokens';

type Draft = Record<AttributeName, number>;

const emptyDraft = (): Draft => ({ strength: 0, speed: 0, skill: 0, endurance: 0, intelligence: 0 });

/** Only the attributes the user raised, as positive whole numbers (the API rejects 0). */
function toAllocations(draft: Draft): AttributeAllocations {
  const result: AttributeAllocations = {};
  for (const name of ATTRIBUTE_NAMES) if (draft[name] > 0) result[name] = draft[name];
  return result;
}

/**
 * Attributes screen: spend unspent points with +/- steppers. Spent points are permanent, so the confirm
 * button first shows a confirmation step. All numbers come from GET /pet; the app only blocks going
 * above `unspent_attribute_points` (the server is the one that enforces it).
 */
export default function AttributesScreen() {
  const { t } = useTranslation();
  const pet = usePet();
  const spend = useSpendAttributes();
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [confirming, setConfirming] = useState(false);
  const [done, setDone] = useState(false);

  const header = (
    <View className="flex-row items-center gap-sm">
      <IconButton icon="chevron-back" accessibilityLabel={t('common.back')} onPress={() => router.back()} />
      <Text variant="title" className="flex-1">
        {t('attributes.title')}
      </Text>
    </View>
  );

  if (pet.isPending) {
    return (
      <Screen>
        {header}
        <Skeleton lines={5} />
      </Screen>
    );
  }
  if (pet.isError) {
    return (
      <Screen>
        {header}
        <ErrorState error={pet.error} onRetry={() => void pet.refetch()} />
      </Screen>
    );
  }

  const data: Pet = pet.data;
  const spent = ATTRIBUTE_NAMES.reduce((sum, name) => sum + draft[name], 0);
  const remaining = Math.max(0, data.unspent_attribute_points - spent);

  const change = (name: AttributeName, delta: number) => {
    setDone(false);
    setDraft((current) => ({ ...current, [name]: Math.max(0, current[name] + delta) }));
  };

  const confirm = () => {
    spend.mutate(toAllocations(draft), {
      onSuccess: () => {
        setDraft(emptyDraft());
        setConfirming(false);
        setDone(true);
      },
      onError: () => {
        // The server keeps the truth (the pet is refetched on NOT_ENOUGH_ATTRIBUTE_POINTS): start over from it.
        setDraft(emptyDraft());
        setConfirming(false);
      },
    });
  };

  const errorText = spend.isError
    ? errorMessage(isApiError(spend.error) ? spend.error.code : 'UNKNOWN_ERROR')
    : null;

  let footer;
  if (confirming) {
    footer = (
      <View testID="confirm-spend" className="gap-sm rounded-lg bg-surface p-lg">
        <Text variant="subtitle">{t('attributes.confirmTitle')}</Text>
        <Text variant="secondary">{t('attributes.confirmBody')}</Text>
        <Button
          testID="confirm-spend-yes"
          label={spend.isPending ? t('attributes.saving') : t('attributes.confirmYes')}
          loading={spend.isPending}
          onPress={confirm}
        />
        <Button
          action="ghost"
          label={t('attributes.confirmBack')}
          disabled={spend.isPending}
          onPress={() => setConfirming(false)}
        />
      </View>
    );
  } else {
    footer = (
      <Button
        testID="spend-attributes"
        label={t('attributes.confirm')}
        disabled={spent === 0}
        onPress={() => {
          spend.reset();
          setDone(false);
          setConfirming(true);
        }}
      />
    );
  }

  return (
    <Screen footer={footer}>
      {header}
      <Text variant="subtitle">{t('attributes.level', { level: data.level })}</Text>

      <View
        testID="remaining-points"
        accessible
        accessibilityLiveRegion="polite"
        accessibilityLabel={t('attributes.remaining', { count: remaining })}
        className="flex-row items-center gap-xs self-start rounded-pill bg-points-bg px-md py-xs"
      >
        <Icon name="star" size={16} color={colors.pointsText} />
        <Text className="font-heading text-points-text">{t('attributes.remaining', { count: remaining })}</Text>
      </View>

      {data.unspent_attribute_points === 0 && !done ? (
        <Text testID="no-points" variant="secondary">
          {t('attributes.none')}
        </Text>
      ) : null}

      <View className="gap-sm">
        {ATTRIBUTE_NAMES.map((name) => {
          const label = t(`attributes.names.${name}`);
          const value = data.attributes[name] + draft[name];
          return (
            <View
              key={name}
              testID={`attribute-${name}`}
              className="min-h-touch flex-row items-center gap-sm rounded-lg bg-surface px-md py-xs"
            >
              <Text className="flex-1 font-heading">{label}</Text>
              <IconButton
                testID={`decrease-${name}`}
                icon="remove-circle-outline"
                accessibilityLabel={t('attributes.decrease', { name: label })}
                disabled={draft[name] === 0 || spend.isPending}
                onPress={() => change(name, -1)}
                color={draft[name] === 0 ? colors.inputBorder : colors.primary}
              />
              <Text
                testID={`value-${name}`}
                accessibilityLabel={t('attributes.value', { name: label, count: value })}
                className="min-w-touch text-center font-heading"
              >
                {value}
              </Text>
              <IconButton
                testID={`increase-${name}`}
                icon="add-circle-outline"
                accessibilityLabel={t('attributes.increase', { name: label })}
                disabled={remaining === 0 || spend.isPending}
                onPress={() => change(name, 1)}
                color={remaining === 0 ? colors.inputBorder : colors.primary}
              />
            </View>
          );
        })}
      </View>

      <Text variant="caption">{t('attributes.permanent')}</Text>
      <Text variant="caption">{t('attributes.displayOnly')}</Text>

      {errorText ? (
        <Text testID="spend-error" accessibilityRole="alert" className="text-danger">
          {errorText}
        </Text>
      ) : null}
      {done ? (
        <View
          testID="spend-success"
          accessibilityRole="alert"
          className="flex-row items-center gap-sm rounded-lg bg-points-bg p-lg"
        >
          <Icon name="checkmark-circle" color={colors.pointsText} />
          <Text className="flex-1 font-heading text-points-text">{t('attributes.success')}</Text>
        </View>
      ) : null}
    </Screen>
  );
}
