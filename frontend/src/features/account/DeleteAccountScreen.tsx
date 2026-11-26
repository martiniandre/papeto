import { useMutation } from '@tanstack/react-query';
import { router } from 'expo-router';
import { useState } from 'react';
import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { api } from '@/api/endpoints';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Checkbox } from '@/components/ui/Checkbox';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';

/** Screen 35: the button stays disabled until the confirmation is checked; then 41. */
export default function DeleteAccountScreen() {
  const { t } = useTranslation();
  const [confirmed, setConfirmed] = useState(false);
  const deleteAccount = useMutation({
    mutationFn: api.deleteAccount,
    // The session is ended on screen 41, outside the tabs, so the sign-out redirect does not race.
    onSuccess: () => router.replace('/(onboarding)/account-deleted'),
  });

  return (
    <Screen
      footer={
        <>
          <Button
            testID="delete-account"
            action="danger"
            label={deleteAccount.isPending ? t('account.delete.deleting') : t('account.delete.action')}
            disabled={!confirmed}
            loading={deleteAccount.isPending}
            accessibilityHint={confirmed ? undefined : t('account.delete.hint')}
            onPress={() => deleteAccount.mutate()}
          />
          {!confirmed ? (
            <Text variant="caption" className="text-center">
              {t('account.delete.hint')}
            </Text>
          ) : null}
          <Button
            testID="keep-account"
            action="secondary"
            label={t('account.delete.keep')}
            disabled={deleteAccount.isPending}
            onPress={() => router.back()}
          />
        </>
      }
    >
      <View className="flex-row items-center gap-sm">
        <IconButton icon="chevron-back" accessibilityLabel={t('common.back')} onPress={() => router.back()} />
        <Text variant="title" className="flex-1">
          {t('account.delete.title')}
        </Text>
      </View>
      <Text>{t('account.delete.lose')}</Text>
      <Text>{t('account.delete.grace')}</Text>
      <Button
        action="ghost"
        label={t('account.delete.exportFirst')}
        onPress={() => router.push('/account/export')}
      />
      <Checkbox
        testID="delete-confirm-checkbox"
        label={t('account.delete.confirm')}
        checked={confirmed}
        onChange={setConfirmed}
      />
      {deleteAccount.isError ? (
        <Text testID="delete-account-failed" accessibilityRole="alert" className="font-semibold">
          {t('account.delete.failed')}
        </Text>
      ) : null}
    </Screen>
  );
}
