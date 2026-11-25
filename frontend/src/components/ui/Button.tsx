import { createButton } from '@gluestack-ui/core/button/creator';
import { tva, useStyleContext, withStyleContext } from '@gluestack-ui/utils/nativewind-utils';
import type { ReactNode } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';

import { colors } from '@/theme/tokens';

const SCOPE = 'BUTTON';

const UIButton = createButton({
  Root: withStyleContext(Pressable, SCOPE),
  Text,
  Group: View,
  Spinner: ActivityIndicator,
  Icon: View,
});

const rootStyle = tva({
  base: 'min-h-touch flex-row items-center justify-center rounded-pill px-xl py-md gap-sm',
  variants: {
    action: {
      primary: 'bg-primary data-[active=true]:opacity-90',
      secondary: 'bg-surface border-2 border-primary',
      ghost: 'bg-transparent',
    },
    isDisabled: { true: 'opacity-50' },
  },
});

const textStyle = tva({
  base: 'font-heading text-body text-center',
  parentVariants: {
    action: {
      primary: 'text-on-primary',
      secondary: 'text-primary',
      ghost: 'text-primary',
    },
  },
});

function ButtonLabel({ children }: { children: ReactNode }) {
  const { action } = useStyleContext(SCOPE) as { action: Action };
  return <UIButton.Text className={textStyle({ parentVariants: { action } })}>{children}</UIButton.Text>;
}

type Action = 'primary' | 'secondary' | 'ghost';

export interface ButtonProps {
  label: string;
  onPress?: () => void;
  action?: Action;
  disabled?: boolean;
  /** Shows a spinner and announces busy state; the button is disabled meanwhile. */
  loading?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  icon?: ReactNode;
  className?: string;
  testID?: string;
}

/** Primary app button (Gluestack button creator styled with NativeWind tokens). */
export function Button({
  label,
  onPress,
  action = 'primary',
  disabled = false,
  loading = false,
  accessibilityLabel,
  accessibilityHint,
  icon,
  className,
  testID,
}: ButtonProps) {
  const isDisabled = disabled || loading;
  return (
    <UIButton
      onPress={onPress}
      isDisabled={isDisabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? label}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: isDisabled, busy: loading }}
      className={rootStyle({ action, isDisabled, class: className })}
      context={{ action }}
      testID={testID}
    >
      {loading ? (
        <UIButton.Spinner color={action === 'primary' ? colors.onPrimary : colors.primary} />
      ) : (
        icon
      )}
      <ButtonLabel>{label}</ButtonLabel>
    </UIButton>
  );
}
