import Ionicons from '@expo/vector-icons/Ionicons';
import type { ComponentProps } from 'react';

export type IconName = ComponentProps<typeof Ionicons>['name'];

interface IconProps {
  name: IconName;
  size?: number;
  color?: string;
}

/** Decorative icon. Icon-only buttons must set their own accessibilityLabel. */
export function Icon({ name, size = 24, color }: IconProps) {
  return (
    <Ionicons
      name={name}
      size={size}
      color={color}
      accessible={false}
      importantForAccessibility="no"
    />
  );
}
