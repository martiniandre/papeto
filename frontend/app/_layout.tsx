import '../global.css';
import '@/i18n';

import {
  Nunito_400Regular,
  Nunito_600SemiBold,
  Nunito_800ExtraBold,
  useFonts,
} from '@expo-google-fonts/nunito';
import { QueryClientProvider } from '@tanstack/react-query';
import { Stack, router, useSegments } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useState } from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { setAdultConfirmationListener } from '@/api/client';
import { createQueryClient } from '@/api/queries';
import { listenForExpiredSession, restoreSession } from '@/features/auth/session';
import { wireOnlineManager } from '@/hooks/useOnline';
import { useSessionStore } from '@/stores/session';
import { colors } from '@/theme/tokens';

void SplashScreen.preventAutoHideAsync();
wireOnlineManager();

export default function RootLayout() {
  const [queryClient] = useState(createQueryClient);
  const [fontsLoaded] = useFonts({ Nunito_400Regular, Nunito_600SemiBold, Nunito_800ExtraBold });
  const status = useSessionStore((state) => state.status);
  const segments = useSegments();

  useEffect(() => {
    listenForExpiredSession(queryClient);
    setAdultConfirmationListener(() => router.replace('/(onboarding)/age-terms'));
    void restoreSession();
    return () => setAdultConfirmationListener(null);
  }, [queryClient]);

  useEffect(() => {
    if (fontsLoaded && status !== 'unknown') void SplashScreen.hideAsync();
  }, [fontsLoaded, status]);

  // Signed out anywhere outside onboarding → back to Sign in.
  useEffect(() => {
    if (status === 'signedOut' && segments[0] !== '(onboarding)') {
      router.replace('/(onboarding)/sign-in');
    }
  }, [status, segments]);

  if (!fontsLoaded || status === 'unknown') return null;

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerShown: false,
            contentStyle: { backgroundColor: colors.background },
          }}
        >
          <Stack.Screen name="index" />
          <Stack.Screen name="(onboarding)" />
          <Stack.Screen name="(tabs)" />
          <Stack.Screen name="meal" options={{ presentation: 'fullScreenModal' }} />
          <Stack.Screen name="meals" />
          <Stack.Screen name="account" />
          <Stack.Screen name="pet" options={{ presentation: 'fullScreenModal' }} />
          <Stack.Screen name="premium" options={{ presentation: 'modal' }} />
        </Stack>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
