import { Pressable } from 'react-native';

import { Icon, type IconName } from '@/components/ui/Icon';
import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

interface IconButtonProps {
  icon: IconName;
  /** Required: icon-only buttons need a label for screen readers. */
  accessibilityLabel: string;
  onPress: () => void;
  color?: string;
  size?: number;
  selected?: boolean;
  disabled?: boolean;
  className?: string;
  testID?: string;
}

export function IconButton({
  icon,
  accessibilityLabel,
  onPress,
  color = colors.text,
  size = 26,
  selected,
  disabled,
  className,
  testID,
}: IconButtonProps) {
  return (
    <Pressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled: !!disabled, selected }}
      disabled={disabled}
      onPress={onPress}
      hitSlop={8}
      className={cn('min-h-touch min-w-touch items-center justify-center rounded-pill', className)}
    >
      <Icon name={icon} size={size} color={color} />
    </Pressable>
  );
}
