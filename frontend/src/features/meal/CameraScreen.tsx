import { CameraView } from 'expo-camera';
import { router } from 'expo-router';
import { useRef, useState } from 'react';
import { View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';

import { Screen } from '@/components/Screen';
import { Button } from '@/components/ui/Button';
import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

import { useSubmitPhoto } from './useSubmitPhoto';

/**
 * Screen 4: live camera, flash on/off, gallery. If the camera cannot mount, falls back to gallery.
 * The low-light hint is static guidance for now (expo-camera exposes no light level).
 */
export default function CameraScreen() {
  const { t } = useTranslation();
  const camera = useRef<CameraView>(null);
  const [flash, setFlash] = useState(false);
  const [ready, setReady] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const { submit, fromGallery, preparing } = useSubmitPhoto();

  const shoot = async () => {
    if (!camera.current || preparing) return;
    const picture = await camera.current.takePictureAsync({ quality: 0.9, exif: false, shutterSound: false });
    if (picture) await submit({ uri: picture.uri, width: picture.width, height: picture.height });
  };

  if (unavailable) {
    return (
      <Screen
        footer={
          <>
            <Button label={t('meal.camera.gallery')} loading={preparing} onPress={() => void fromGallery()} />
            <Button action="ghost" label={t('common.back')} onPress={() => router.back()} />
          </>
        }
      >
        <Text variant="title">{t('meal.camera.title')}</Text>
        <Text>{t('meal.camera.noCamera')}</Text>
      </Screen>
    );
  }

  return (
    <View className="flex-1 bg-ink">
      <CameraView
        ref={camera}
        style={{ flex: 1 }}
        facing="back"
        flash={flash ? 'on' : 'off'}
        onCameraReady={() => setReady(true)}
        onMountError={() => setUnavailable(true)}
        accessible={false}
      />
      <SafeAreaView className="absolute inset-0 justify-between" edges={['top', 'bottom']}>
        <View className="flex-row items-center justify-between px-md">
          <IconButton
            icon="close"
            color={colors.onPrimary}
            accessibilityLabel={t('meal.camera.close')}
            onPress={() => router.back()}
          />
          <IconButton
            testID="flash-toggle"
            icon={flash ? 'flash' : 'flash-off'}
            color={colors.onPrimary}
            selected={flash}
            accessibilityLabel={flash ? t('meal.camera.flashOn') : t('meal.camera.flashOff')}
            onPress={() => setFlash((value) => !value)}
          />
        </View>
        <View className="items-center gap-md px-lg pb-lg">
          <Text className="rounded-md bg-ink px-md py-xs text-center text-on-primary">
            {preparing ? t('meal.camera.preparing') : t('meal.camera.hint')}
          </Text>
          <View className="w-full flex-row items-center justify-between">
            <IconButton
              icon="images-outline"
              color={colors.onPrimary}
              accessibilityLabel={t('meal.camera.gallery')}
              onPress={() => void fromGallery()}
              disabled={preparing}
            />
            <IconButton
              testID="shutter"
              icon="radio-button-on"
              size={72}
              color={colors.onPrimary}
              accessibilityLabel={t('meal.camera.shutter')}
              onPress={() => void shoot()}
              disabled={!ready || preparing}
            />
            <View className="min-w-touch" />
          </View>
        </View>
      </SafeAreaView>
    </View>
  );
}
