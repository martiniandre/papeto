import { useMutation, useQueryClient } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { api } from '@/api/endpoints';
import { queryKeys } from '@/api/queries';
import type { MealType } from '@/api/types';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';
import { errorMessage } from '@/i18n';
import { useMealFlowStore } from '@/stores/mealFlow';
import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

const TYPES: MealType[] = ['breakfast', 'lunch', 'snack', 'dinner'];
/** Backend limits for POST /meals/manual: 1 to 30 items of 1 to 80 characters. */
export const MAX_MANUAL_ITEMS = 30;
const MAX_ITEM_LENGTH = 80;

/** Picks a default meal type from the local hour (the user can change it). */
export function guessMealType(now = new Date()): MealType {
  const hour = now.getHours();
  if (hour < 10) return 'breakfast';
  if (hour < 15) return 'lunch';
  if (hour < 18) return 'snack';
  return 'dinner';
}

/**
 * RF-95: when the photo cannot be read, pick the foods and the meal type by hand (POST /meals/manual).
 * It counts as a log for the pet, never calls the AI and never talks about the photo limit.
 */
export default function ManualEntryScreen() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const setResult = useMealFlowStore((state) => state.setResult);
  const [mealType, setMealType] = useState<MealType>(() => guessMealType());
  const [items, setItems] = useState<string[]>([]);
  const [draft, setDraft] = useState('');
  const common = t('meal.manual.common', { returnObjects: true }) as unknown as string[];

  const submit = useMutation({
    mutationFn: () => api.createManualMeal({ items, meal_type: mealType }),
    onSuccess: (created) => {
      setResult(created);
      queryClient.setQueryData(queryKeys.pet, created.pet);
      void queryClient.invalidateQueries({ queryKey: queryKeys.mealsAll });
      router.replace('/meal/result');
    },
    onError: (error) => {
      if (isApiError(error) && error.code === 'MEAL_CONSENT_REQUIRED') {
        router.replace('/(onboarding)/age-terms');
      }
    },
  });

  const toggle = (item: string) =>
    setItems((current) =>
      current.includes(item)
        ? current.filter((other) => other !== item)
        : current.length < MAX_MANUAL_ITEMS
          ? [...current, item]
          : current,
    );

  const addDraft = () => {
    const value = draft.trim();
    if (value && !items.includes(value) && items.length < MAX_MANUAL_ITEMS) setItems([...items, value]);
    setDraft('');
  };

  const customItems = items.filter((item) => !common.includes(item));

  return (
    <Screen
      footer={
        <Button
          testID="manual-submit"
          label={submit.isPending ? t('meal.manual.submitting') : t('meal.manual.submit')}
          loading={submit.isPending}
          disabled={items.length === 0}
          onPress={() => submit.mutate()}
        />
      }
    >
      <View className="flex-row items-center gap-sm">
        <IconButton
          icon="chevron-back"
          accessibilityLabel={t('common.back')}
          onPress={() => router.replace('/(tabs)/home')}
        />
        <Text variant="title" className="flex-1">
          {t('meal.manual.title')}
        </Text>
      </View>
      <Text variant="secondary">{t('meal.manual.body')}</Text>

      <View className="gap-sm">
        <Text variant="caption">{t('meal.manual.typeLabel')}</Text>
        <View accessibilityRole="radiogroup" className="flex-row gap-sm">
          {TYPES.map((type) => {
            const selected = type === mealType;
            return (
              <Pressable
                key={type}
                testID={`manual-type-${type}`}
                accessibilityRole="radio"
                accessibilityLabel={t(`meal.types.${type}`)}
                accessibilityState={{ selected, checked: selected }}
                onPress={() => setMealType(type)}
                className={cn(
                  'min-h-touch flex-1 flex-row items-center justify-center gap-xs rounded-md border-2 px-xs',
                  selected ? 'border-primary bg-primary' : 'border-input-border bg-surface',
                )}
              >
                {selected ? <Icon name="checkmark" size={16} color={colors.onPrimary} /> : null}
                <Text
                  className={cn('text-center', selected ? 'font-heading text-on-primary' : 'font-semibold')}
                >
                  {t(`meal.typesShort.${type}`)}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View className="gap-sm">
        <Text variant="caption">{t('meal.manual.commonLabel')}</Text>
        <View className="flex-row flex-wrap gap-sm">
          {common.map((item) => {
            const selected = items.includes(item);
            return (
              <Pressable
                key={item}
                testID="manual-food"
                accessibilityRole="checkbox"
                accessibilityLabel={item}
                accessibilityState={{ checked: selected }}
                onPress={() => toggle(item)}
                className={cn(
                  'min-h-touch flex-row items-center gap-xs rounded-pill border-2 px-md',
                  selected ? 'border-primary bg-primary' : 'border-input-border bg-surface',
                )}
              >
                {selected ? <Icon name="checkmark" size={16} color={colors.onPrimary} /> : null}
                <Text className={selected ? 'font-heading text-on-primary' : 'font-semibold'}>{item}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {customItems.length > 0 ? (
        <View className="gap-sm">
          <Text variant="caption">{t('meal.manual.selectedLabel')}</Text>
          {customItems.map((item) => (
            <View
              key={item}
              testID="manual-custom-item"
              className="min-h-touch flex-row items-center justify-between gap-sm rounded-md bg-surface pl-md"
            >
              <Text className="flex-1 font-semibold">{item}</Text>
              <IconButton
                icon="close"
                accessibilityLabel={t('meal.manual.removeItem', { item })}
                onPress={() => toggle(item)}
              />
            </View>
          ))}
        </View>
      ) : null}

      <TextField
        testID="manual-new-item"
        label={t('meal.manual.addLabel')}
        placeholder={t('meal.manual.addPlaceholder')}
        value={draft}
        onChangeText={setDraft}
        onSubmitEditing={addDraft}
        returnKeyType="done"
        maxLength={MAX_ITEM_LENGTH}
      />
      <Button
        testID="manual-add"
        action="secondary"
        label={t('meal.manual.add')}
        icon={<Icon name="add" color={colors.primary} />}
        disabled={draft.trim().length === 0 || items.length >= MAX_MANUAL_ITEMS}
        onPress={addDraft}
      />

      {items.length === 0 ? (
        <Text accessibilityLiveRegion="polite" variant="secondary">
          {t('meal.manual.noneSelected')}
        </Text>
      ) : null}
      {submit.isError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {isApiError(submit.error) && submit.error.code !== 'UNKNOWN_ERROR'
            ? errorMessage(submit.error.code)
            : t('meal.manual.saveError')}
        </Text>
      ) : null}
    </Screen>
  );
}
