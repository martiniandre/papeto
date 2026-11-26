import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Text } from '@/components/ui/Text';

import { undoMealDelete, usePendingDeleteStore } from './pendingDelete';

/** Screen 42: "Refeição apagada" + "Desfazer" while the 5 s undo window is open. */
export function UndoSnackbar() {
  const { t } = useTranslation();
  const pendingId = usePendingDeleteStore((state) => state.pendingId);
  const failed = usePendingDeleteStore((state) => state.failed);

  if (pendingId) {
    return (
      <View
        testID="undo-snackbar"
        accessibilityRole="alert"
        accessibilityLiveRegion="polite"
        className="absolute inset-x-lg bottom-lg min-h-touch flex-row items-center justify-between gap-md rounded-md bg-ink px-lg"
      >
        <Text className="flex-1 font-semibold text-on-primary">{t('history.deleted')}</Text>
        <Pressable
          testID="undo-button"
          accessibilityRole="button"
          accessibilityLabel={t('history.undo')}
          onPress={undoMealDelete}
          className="min-h-touch min-w-touch items-center justify-center"
        >
          <Text className="font-heading text-on-primary underline">{t('history.undo')}</Text>
        </Pressable>
      </View>
    );
  }
  if (failed) {
    return (
      <View
        testID="delete-failed"
        accessibilityRole="alert"
        className="absolute inset-x-lg bottom-lg min-h-touch justify-center rounded-md bg-ink px-lg py-sm"
      >
        <Text className="text-on-primary">{t('history.deleteFailed')}</Text>
      </View>
    );
  }
  return null;
}
