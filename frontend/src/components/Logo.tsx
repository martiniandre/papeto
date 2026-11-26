import { Image } from 'react-native';
import { useTranslation } from 'react-i18next';

export function Logo({ width = 180 }: { width?: number }) {
  const { t } = useTranslation();
  return (
    <Image
      source={require('../../assets/brand/logo.png')}
      accessibilityRole="image"
      accessibilityLabel={t('brand.logoLabel')}
      resizeMode="contain"
      style={{ width, height: (width * 294) / 1000 }}
    />
  );
}
