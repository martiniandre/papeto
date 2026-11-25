import { router } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { usePet } from '@/api/queries';
import { Pet } from '@/components/Pet';
import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';

import { requestNotifications, snoozeNotificationsPrompt } from './notificationsPrompt';

/** Screen 31: after the first meal. "Agora não" does not ask again for 7 days. */
export default function AllowNotificationsScreen() {
  const { t } = useTranslation();
  const pet = usePet();
  const name = pet.data?.name ?? t("pet.defaultName");

  const allow = async () => {
    await requestNotifications().catch(() => false);
    router.replace('/(tabs)/home');
  };
  const later = async () => {
    await snoozeNotificationsPrompt().catch(() => undefined);
    router.replace('/(tabs)/home');
  };

  return (
    <Screen
      footer={
        <>
          <Button label={t('meal.notifications.allow')} onPress={() => void allow()} />
          <Button action="ghost" label={t('common.notNow')} onPress={() => void later()} />
        </>
      }
    >
      <Pet mood={pet.data?.mood ?? 'happy'} name={name} size={180} className="self-center" />
      <Text variant="title" className="text-center">
        {t('meal.notifications.title')}
      </Text>
      <Text variant="secondary" className="text-center">
        {t('meal.notifications.body', { name })}
      </Text>
    </Screen>
  );
}
