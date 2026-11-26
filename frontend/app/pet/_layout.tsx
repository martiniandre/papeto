import { Stack } from 'expo-router';

import { colors } from '@/theme/tokens';

/** Flow 6: lost a life (28) and fainted (12), shown over Home when the app opens. */
export default function PetLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        gestureEnabled: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    />
  );
}
