import { useCameraPermissions } from 'expo-camera';
import { router } from 'expo-router';
import { Linking } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

import { useSubmitPhoto } from './useSubmitPhoto';

/** Screen 9: first request; denied before ("Abrir Ajustes"); gallery only. */
export default function CameraPermissionScreen() {
  const { t } = useTranslation();
  const [permission, requestPermission] = useCameraPermissions();
  const { fromGallery, preparing } = useSubmitPhoto();
  const deniedForGood = permission?.granted === false && permission.canAskAgain === false;

  const allow = async () => {
    const response = await requestPermission();
    if (response.granted) router.replace('/meal/camera');
  };

  return (
    <Screen
      footer={
        <>
          {deniedForGood ? (
            <Button label={t('common.openSettings')} onPress={() => void Linking.openSettings()} />
          ) : (
            <Button testID="allow-camera" label={t('meal.permission.allow')} onPress={() => void allow()} />
          )}
          <Button
            action="secondary"
            label={t('meal.permission.gallery')}
            loading={preparing}
            onPress={() => void fromGallery()}
          />
          <Button action="ghost" label={t('common.back')} onPress={() => router.back()} />
        </>
      }
    >
      <Icon name="camera-outline" size={56} color={colors.primary} />
      <Text variant="title">{t('meal.permission.title')}</Text>
      <Text variant="secondary">
        {deniedForGood ? t('meal.permission.deniedBody') : t('meal.permission.body')}
      </Text>
    </Screen>
  );
}
