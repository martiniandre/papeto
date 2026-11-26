import { Linking, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import { Button } from '@/components/ui/Button';
import { Icon } from '@/components/ui/Icon';
import { CVV_PHONE_URL, CVV_SITE_URL } from '@/config';
import { colors } from '@/theme/tokens';

/** The support path: CVV 188 (phone) and cvv.org.br (chat). Shared by Profile > Apoio and the Home card. */
export function SupportPath() {
  const { t } = useTranslation();
  return (
    <View className="gap-sm">
      <Button
        testID="support-call"
        label={t('support.call')}
        accessibilityLabel={t('support.callLabel')}
        icon={<Icon name="call-outline" color={colors.onPrimary} />}
        onPress={() => void Linking.openURL(CVV_PHONE_URL)}
      />
      <Button
        testID="support-site"
        action="secondary"
        label={t('support.site')}
        accessibilityLabel={t('support.siteLabel')}
        onPress={() => void Linking.openURL(CVV_SITE_URL)}
      />
    </View>
  );
}
