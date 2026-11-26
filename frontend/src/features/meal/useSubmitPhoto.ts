import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { useCallback, useState } from 'react';

import { useMealFlowStore } from '@/stores/mealFlow';

import { type CapturedPhoto, discardPhoto, resizePhoto } from './photo';

/** Opens the system gallery (no media-library permission needed with the system picker). */
export async function pickFromGallery(): Promise<CapturedPhoto | null> {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    quality: 1,
    allowsMultipleSelection: false,
    exif: false,
  });
  if (result.canceled || !result.assets[0]) return null;
  const asset = result.assets[0];
  return { uri: asset.uri, width: asset.width, height: asset.height };
}

/** Resizes a captured or picked photo, drops the original, and moves to Analyzing (5). */
export function useSubmitPhoto() {
  const setPhoto = useMealFlowStore((state) => state.setPhoto);
  const [preparing, setPreparing] = useState(false);

  const submit = useCallback(
    async (photo: CapturedPhoto) => {
      setPreparing(true);
      try {
        const resized = await resizePhoto(photo);
        if (resized !== photo.uri) discardPhoto(photo.uri);
        setPhoto(resized);
        router.replace('/meal/analyzing');
      } finally {
        setPreparing(false);
      }
    },
    [setPhoto],
  );

  const fromGallery = useCallback(async () => {
    const photo = await pickFromGallery();
    if (photo) await submit(photo);
  }, [submit]);

  return { submit, fromGallery, preparing };
}
