import { View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { isApiError, NETWORK_ERROR } from '@/api/client';
import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { Text } from '@/components/ui/Text';
import { errorMessage } from '@/i18n';
import { colors } from '@/theme/tokens';

interface ErrorStateProps {
  error: unknown;
  onRetry: () => void;
}

/** Server or network error with "Tentar de novo". */
export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const { t } = useTranslation();
  const offline = isApiError(error) && error.code === NETWORK_ERROR;
  const message = isApiError(error) ? errorMessage(error.code) : t('common.serverError');
  return (
    <View testID="error-state" accessibilityRole="alert" className="items-center gap-md py-xl">
      <Icon
        name={offline ? 'cloud-offline-outline' : 'alert-circle-outline'}
        size={40}
        color={colors.textSecondary}
      />
      <Text className="text-center">{message}</Text>
      <Button label={t('common.retry')} action="secondary" onPress={onRetry} />
    </View>
  );
}
