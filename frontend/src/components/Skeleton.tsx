import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

interface SkeletonProps {
  lines?: number;
  /** Show a big block on top (pet area). */
  hero?: boolean;
}

/** Loading placeholder. Announced once as "Carregando". */
export function Skeleton({ lines = 3, hero = false }: SkeletonProps) {
  const { t } = useTranslation();
  return (
    <View
      testID="skeleton"
      accessible
      accessibilityLabel={t('common.loading')}
      accessibilityState={{ busy: true }}
      className="gap-md"
    >
      {hero ? <View className="aspect-square w-full rounded-lg bg-surface" /> : null}
      {Array.from({ length: lines }, (_, index) => (
        <View key={index} className="min-h-touch w-full rounded-md bg-surface" />
      ))}
    </View>
  );
}
