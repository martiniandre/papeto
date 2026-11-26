import { Stack } from 'expo-router';
import { useTranslation } from 'react-i18next';

import { colors, fonts } from '@/theme/tokens';

export default function OnboardingLayout() {
  const { t } = useTranslation();
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        headerShadowVisible: false,
        headerTitle: '',
        headerBackButtonDisplayMode: 'minimal',
        headerTintColor: colors.primary,
        headerStyle: { backgroundColor: colors.background },
        headerTitleStyle: { fontFamily: fonts.bold },
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="sign-in" />
      <Stack.Screen name="email" options={{ headerShown: true, title: t('auth.email.title') }} />
      <Stack.Screen
        name="create-account"
        options={{ headerShown: true, title: t('auth.register.title') }}
      />
      <Stack.Screen
        name="recover-password"
        options={{ headerShown: true, title: t('auth.recover.title') }}
      />
      <Stack.Screen
        name="reset-password"
        options={{ headerShown: true, title: t('auth.reset.title') }}
      />
      <Stack.Screen name="age-terms"options={{ gestureEnabled: false }} />
      <Stack.Screen name="name-pet" options={{ gestureEnabled: false }} />
      <Stack.Screen name="meet-pet" options={{ gestureEnabled: false }} />
      <Stack.Screen name="how-lives-work" />
      <Stack.Screen name="account-deleted" options={{ gestureEnabled: false }} />
    </Stack>
  );
}
