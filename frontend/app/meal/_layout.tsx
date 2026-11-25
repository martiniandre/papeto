import { Stack } from 'expo-router';

import { colors } from '@/theme/tokens';

/** Flow 2 (log a meal), presented over the tabs. */
export default function MealLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="camera-permission" />
      <Stack.Screen name="camera" />
      <Stack.Screen name="analyzing" options={{ gestureEnabled: false }} />
      <Stack.Screen name="result" options={{ gestureEnabled: false }} />
      <Stack.Screen name="error" />
      <Stack.Screen name="daily-limit" />
      <Stack.Screen name="notifications" options={{ gestureEnabled: false }} />
    </Stack>
  );
}
