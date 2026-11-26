import { Pressable, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

export interface ToggleRowProps {
  label: string;
  value: boolean;
  onChange: (value: boolean) => void;
  /** Secondary line, e.g. the quiet-hours range. */
  detail?: string;
  disabled?: boolean;
  testID?: string;
}

/** Switch row. The state is shown as a check icon plus "Ligado"/"Desligado" text (not by color only). */
export function ToggleRow({ label, value, onChange, detail, disabled, testID }: ToggleRowProps) {
  const { t } = useTranslation();
  return (
    <Pressable
      testID={testID}
      accessibilityRole="switch"
      accessibilityLabel={detail ? `${label}, ${detail}` : label}
      accessibilityState={{ checked: value, disabled: !!disabled }}
      disabled={disabled}
      onPress={() => onChange(!value)}
      className={cn('min-h-touch flex-row items-center gap-md py-sm', disabled && 'opacity-50')}
    >
      <View className="flex-1">
        <Text className="font-semibold">{label}</Text>
        {detail ? <Text variant="secondary">{detail}</Text> : null}
      </View>
      <View
        className={cn(
          'min-h-touch min-w-touch flex-row items-center justify-center gap-xs rounded-pill border-2 px-md',
          value ? 'border-primary bg-primary' : 'border-input-border bg-surface',
        )}
      >
        {value ? <Icon name="checkmark" size={16} color={colors.onPrimary} /> : null}
        <Text className={cn('text-caption', value ? 'font-heading text-on-primary' : 'font-semibold')}>
          {value ? t('account.on') : t('account.off')}
        </Text>
      </View>
    </Pressable>
  );
}
