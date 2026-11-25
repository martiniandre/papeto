import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';

/** Points total in the amber token pair. Points are only ever positive. */
export function PointsBadge({ points }: { points: number }) {
  const { t } = useTranslation();
  return (
    <View
      testID="points-badge"
      accessible
      accessibilityLabel={t('home.points', { count: points })}
      className="flex-row items-center gap-xs self-start rounded-pill bg-points-bg px-md py-xs"
    >
      <Icon name="star" size={16} color={colors.pointsText} />
      <Text className="font-heading text-points-text">{t('home.points', { count: points })}</Text>
    </View>
  );
}
