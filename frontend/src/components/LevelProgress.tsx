import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import type { LevelProgress as LevelProgressData } from '@/api/types';
import { Text } from '@/components/ui/Text';

interface LevelProgressProps {
  level: number;
  progress: LevelProgressData;
}

/** Level and the bar toward the next one. Every number comes from the API; the width is only a ratio of them. */
export function LevelProgress({ level, progress }: LevelProgressProps) {
  const { t } = useTranslation();
  const span = progress.next_level_at - progress.current_level_at;
  const ratio = span > 0 ? (progress.points - progress.current_level_at) / span : 0;
  const percent = Math.round(Math.min(1, Math.max(0, ratio)) * 100);
  const detail = t('home.levelProgress', { points: progress.points, next: progress.next_level_at });

  return (
    <View testID="level-progress" className="gap-xs">
      <Text variant="subtitle" className="text-center">
        {t('home.level', { level })}
      </Text>
      <View
        testID="level-progress-bar"
        accessible
        accessibilityRole="progressbar"
        accessibilityLabel={`${t('home.level', { level })}. ${detail}`}
        accessibilityValue={{ min: 0, max: 100, now: percent }}
        className="h-3 w-full overflow-hidden rounded-pill bg-points-bg"
      >
        <View className="h-3 rounded-pill bg-primary" style={{ width: `${percent}%` }} />
      </View>
      <Text variant="caption" className="text-center">
        {detail}
      </Text>
    </View>
  );
}
