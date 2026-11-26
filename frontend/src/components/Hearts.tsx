import { View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { useTranslation } from 'react-i18next';

import { colors } from '@/theme/tokens';

const HEART =
  'M12 21s-7.5-4.6-9.6-9.1C.9 8.6 2.9 4.5 6.7 4.5c2.1 0 3.6 1.1 4.3 2.4.7-1.3 2.2-2.4 4.3-2.4 3.8 0 5.8 4.1 4.3 7.4C19.5 16.4 12 21 12 21z';

interface HeartsProps {
  lives: number;
  max: number;
  size?: number;
}

/** Lives from the API. Empty hearts use the 3:1 border token; the count is announced as text. */
export function Hearts({ lives, max, size = 28 }: HeartsProps) {
  const { t } = useTranslation();
  return (
    <View
      testID="hearts"
      accessible
      accessibilityRole="text"
      accessibilityLabel={t('hearts.a11y', { lives, max })}
      className="flex-row gap-xs"
    >
      {Array.from({ length: max }, (_, index) => {
        const full = index < lives;
        return (
          <Svg key={index} width={size} height={size} viewBox="0 0 24 24" testID={full ? 'heart-full' : 'heart-empty'}>
            <Path
              d={HEART}
              fill={full ? colors.primary : 'none'}
              stroke={full ? colors.primary : colors.inputBorder}
              strokeWidth={2}
            />
          </Svg>
        );
      })}
    </View>
  );
}
