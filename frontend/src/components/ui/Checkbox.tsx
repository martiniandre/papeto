import { Pressable, View } from 'react-native';

import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

export interface CheckboxProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  testID?: string;
  emphasized?: boolean;
}

/** Checkbox whose checked state is shown by a check icon (not by color only) and announced. */
export function Checkbox({ label, checked, onChange, testID, emphasized }: CheckboxProps) {
  return (
    <Pressable
      testID={testID}
      accessibilityRole="checkbox"
      accessibilityLabel={label}
      accessibilityState={{ checked }}
      onPress={() => onChange(!checked)}
      className={cn(
        'min-h-touch flex-row items-start gap-md rounded-md p-md',
        emphasized ? 'border-2 border-primary bg-surface' : 'bg-surface',
      )}
    >
      <View
        className={cn(
          'mt-xs h-7 w-7 items-center justify-center rounded-sm border-2',
          checked ? 'border-primary bg-primary' : 'border-input-border bg-surface',
        )}
      >
        {checked ? <Icon name="checkmark" size={18} color={colors.onPrimary} /> : null}
      </View>
      <Text className="flex-1">{label}</Text>
    </Pressable>
  );
}
