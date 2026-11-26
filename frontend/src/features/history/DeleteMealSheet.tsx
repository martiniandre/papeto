import { Modal, Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Button } from '@/components/ui/Button';
import { Text } from '@/components/ui/Text';
import { useReduceMotion } from '@/hooks/useReduceMotion';

interface DeleteMealSheetProps {
  visible: boolean;
  onConfirm: () => void;
  onKeep: () => void;
}

/** Screen 37: bottom sheet. Neutral copy: deleting never changes points or lives (pet-rules.md). */
export function DeleteMealSheet({ visible, onConfirm, onKeep }: DeleteMealSheetProps) {
  const { t } = useTranslation();
  const reduceMotion = useReduceMotion();
  return (
    <Modal
      visible={visible}
      transparent
      animationType={reduceMotion ? 'none' : 'slide'}
      onRequestClose={onKeep}
    >
      <View className="flex-1 justify-end bg-black/40">
        <Pressable
          accessible={false}
          importantForAccessibility="no"
          className="flex-1"
          onPress={onKeep}
        />
        <View
          testID="delete-sheet"
          accessibilityViewIsModal
          className="gap-md rounded-t-lg bg-surface px-lg pb-xl pt-lg"
        >
          <Text variant="title">{t('meal.delete.title')}</Text>
          <Text variant="secondary">{t('meal.delete.body')}</Text>
          <Button testID="delete-confirm" action="danger" label={t('meal.delete.confirm')} onPress={onConfirm} />
          <Button testID="delete-keep" action="secondary" label={t('meal.delete.keep')} onPress={onKeep} />
        </View>
      </View>
    </Modal>
  );
}
