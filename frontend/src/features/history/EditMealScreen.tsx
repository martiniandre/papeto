import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { useMeal, useUpdateMeal } from '@/api/queries';
import type { MealType } from '@/api/types';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';
import { errorMessage } from '@/i18n';
import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

const TYPES: MealType[] = ['breakfast', 'lunch', 'snack', 'dinner'];
/** Backend limit: at most 30 items (MealPatch). */
export const MAX_ITEMS = 30;

/** Screen 26: correct meal type and items. Points never change. */
export default function EditMealScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const meal = useMeal(String(id));

  if (meal.isPending) {
    return (
      <Screen>
        <Skeleton lines={5} />
      </Screen>
    );
  }
  if (meal.isError) {
    return (
      <Screen>
        <ErrorState error={meal.error} onRetry={() => void meal.refetch()} />
      </Screen>
    );
  }
  return <EditForm id={String(id)} initialType={meal.data.meal_type} initialItems={meal.data.items} />;
}

function EditForm({
  id,
  initialType,
  initialItems,
}: {
  id: string;
  initialType: MealType;
  initialItems: string[];
}) {
  const { t } = useTranslation();
  const update = useUpdateMeal(id);
  const [mealType, setMealType] = useState<MealType>(initialType);
  const [items, setItems] = useState<string[]>(initialItems);
  const [draft, setDraft] = useState('');

  const addItem = () => {
    const value = draft.trim();
    if (value && items.length < MAX_ITEMS && !items.includes(value)) {
      setItems([...items, value]);
    }
    setDraft('');
  };

  const save = async () => {
    try {
      await update.mutateAsync({ meal_type: mealType, items });
      router.back();
    } catch {
      // The error is shown below from the mutation state.
    }
  };

  return (
    <Screen
      footer={
        <Button
          testID="edit-save"
          label={update.isPending ? t('meal.edit.saving') : t('meal.edit.save')}
          loading={update.isPending}
          disabled={items.length === 0}
          onPress={() => void save()}
        />
      }
    >
      <View className="flex-row items-center gap-sm">
        <IconButton
          icon="chevron-back"
          accessibilityLabel={t('common.back')}
          onPress={() => router.back()}
        />
        <Text variant="title" className="flex-1">
          {t('meal.edit.title')}
        </Text>
      </View>
      <Text variant="secondary">{t('meal.edit.body')}</Text>

      <View className="gap-sm">
        <Text variant="caption">{t('meal.edit.typeLabel')}</Text>
        <View accessibilityRole="radiogroup" className="flex-row gap-sm">
          {TYPES.map((type) => {
            const selected = type === mealType;
            const label = t(`meal.types.${type}`);
            return (
              <Pressable
                key={type}
                testID={`type-${type}`}
                accessibilityRole="radio"
                accessibilityLabel={label}
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
        <Text variant="caption">{t('meal.edit.itemsLabel')}</Text>
        <View className="gap-sm">
          {items.map((item) => (
            <View
              key={item}
              testID="edit-item"
              className="min-h-touch flex-row items-center justify-between gap-sm rounded-md bg-surface pl-md"
            >
              <Text className="flex-1 font-semibold">{item}</Text>
              <IconButton
                icon="close"
                accessibilityLabel={t('meal.edit.removeItem', { item })}
                onPress={() => setItems(items.filter((other) => other !== item))}
              />
            </View>
          ))}
        </View>
        {items.length === 0 ? (
          <Text accessibilityLiveRegion="polite" className="font-semibold">
            {t('meal.edit.noItems')}
          </Text>
        ) : null}
      </View>

      <TextField
        testID="edit-new-item"
        label={t('meal.edit.addLabel')}
        placeholder={t('meal.edit.addPlaceholder')}
        value={draft}
        onChangeText={setDraft}
        onSubmitEditing={addItem}
        returnKeyType="done"
        maxLength={60}
      />
      <Button
        testID="edit-add"
        action="secondary"
        label={t('meal.edit.add')}
        icon={<Icon name="add" color={colors.primary} />}
        disabled={draft.trim().length === 0 || items.length >= MAX_ITEMS}
        onPress={addItem}
      />
      {update.isError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {isApiError(update.error) && update.error.code !== 'UNKNOWN_ERROR'
            ? errorMessage(update.error.code)
            : t('meal.edit.saveError')}
        </Text>
      ) : null}
    </Screen>
  );
}
