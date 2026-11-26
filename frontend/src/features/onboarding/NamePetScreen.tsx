import { zodResolver } from '@hookform/resolvers/zod';
import { router } from 'expo-router';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError } from '@/api/client';
import { useUpdatePet } from '@/api/queries';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { TextField } from '@/components/ui/TextField';
import { errorMessage } from '@/i18n';

import { PET_NAME_MAX, petNameSchema, type PetNameValues } from './schemas';

/** Screen 43: the pet stays hidden until it has a name. Max 20 chars, 3 suggestions. */
export default function NamePetScreen() {
  const { t } = useTranslation();
  const updatePet = useUpdatePet();
  const suggestions = t('onboarding.name.suggestionsList', { returnObjects: true }) as string[];
  const {
    control,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<PetNameValues>({
    resolver: zodResolver(petNameSchema),
    defaultValues: { name: '' },
  });
  const name = useWatch({ control, name: 'name' });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await updatePet.mutateAsync({ name: values.name.trim() });
      router.replace('/(onboarding)/meet-pet');
    } catch {
      // Error shown below from the mutation state.
    }
  });

  return (
    <Screen
      footer={
        <Button
          testID="name-continue"
          label={updatePet.isPending ? t('onboarding.name.saving') : t('common.continue')}
          disabled={name.trim().length === 0}
          loading={updatePet.isPending}
          onPress={onSubmit}
        />
      }
    >
      <Text variant="title">{t('onboarding.name.title')}</Text>
      <Text variant="secondary">{t('onboarding.name.body')}</Text>
      <Controller
        control={control}
        name="name"
        render={({ field }) => (
          <TextField
            testID="pet-name-input"
            label={t('onboarding.name.label')}
            placeholder={t('onboarding.name.placeholder')}
            value={field.value}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            maxLength={PET_NAME_MAX}
            autoCapitalize="words"
            helper={t('onboarding.name.counter', { count: field.value.length, max: PET_NAME_MAX })}
            error={errors.name ? t('onboarding.name.tooLong') : undefined}
          />
        )}
      />
      <View className="gap-sm">
        <Text variant="subtitle">{t('onboarding.name.suggestions')}</Text>
        <View className="flex-row flex-wrap gap-sm">
          {suggestions.map((suggestion) => {
            const selected = name === suggestion;
            return (
              <Pressable
                key={suggestion}
                testID={`suggestion-${suggestion}`}
                accessibilityRole="button"
                accessibilityLabel={selected ? `${suggestion}, ${t('common.selected')}` : suggestion}
                accessibilityState={{ selected }}
                onPress={() => setValue('name', suggestion, { shouldValidate: true })}
                className={
                  selected
                    ? 'min-h-touch justify-center rounded-pill border-2 border-primary bg-primary px-lg'
                    : 'min-h-touch justify-center rounded-pill border-2 border-input-border bg-surface px-lg'
                }
              >
                <Text className={selected ? 'font-heading text-on-primary' : 'font-semibold'}>
                  {selected ? `✓ ${suggestion}` : suggestion}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>
      {updatePet.isError ? (
        <Text accessibilityRole="alert" className="font-semibold">
          {isApiError(updatePet.error) ? errorMessage(updatePet.error.code) : t('common.serverError')}
        </Text>
      ) : null}
    </Screen>
  );
}
