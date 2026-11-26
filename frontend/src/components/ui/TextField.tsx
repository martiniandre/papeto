import { useState } from 'react';
import { TextInput, View, type TextInputProps } from 'react-native';
import { useTranslation } from 'react-i18next';

import { IconButton } from '@/components/ui/IconButton';
import { Text } from '@/components/ui/Text';
import { colors } from '@/theme/tokens';
import { cn } from '@/utils/cn';

export interface TextFieldProps extends Omit<TextInputProps, 'onChange'> {
  label: string;
  error?: string;
  helper?: string;
  /** Adds a show/hide toggle (password fields). */
  secureToggle?: boolean;
}

/** Labelled input. Border uses the 3:1 token `#7D839A`; height grows with font size. */
export function TextField({ label, error, helper, secureToggle, testID, ...props }: TextFieldProps) {
  const { t } = useTranslation();
  const [hidden, setHidden] = useState(true);
  return (
    <View className="gap-xs">
      <Text variant="subtitle" nativeID={`${testID ?? label}-label`}>
        {label}
      </Text>
      <View
        className={cn(
          'min-h-touch flex-row items-center rounded-md border-2 bg-surface px-md',
          error ? 'border-ink' : 'border-input-border',
        )}
      >
        <TextInput
          testID={testID}
          accessibilityLabel={label}
          accessibilityHint={error ?? helper}
          placeholderTextColor={colors.textSecondary}
          secureTextEntry={secureToggle ? hidden : props.secureTextEntry}
          className="min-h-touch flex-1 py-sm font-body text-body text-ink"
          {...props}
        />
        {secureToggle ? (
          <IconButton
            icon={hidden ? 'eye-outline' : 'eye-off-outline'}
            accessibilityLabel={hidden ? t('auth.email.showPassword') : t('auth.email.hidePassword')}
            onPress={() => setHidden((value) => !value)}
          />
        ) : null}
      </View>
      {error ? (
        <Text accessibilityLiveRegion="polite" className="font-semibold">
          {error}
        </Text>
      ) : helper ? (
        <Text variant="secondary">{helper}</Text>
      ) : null}
    </View>
  );
}
