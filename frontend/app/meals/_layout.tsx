import { Stack } from 'expo-router';

import { colors } from '@/theme/tokens';

/** Flow 3: meal detail (25) and correct meal (26), pushed over the tabs. */
export default function MealsLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    />
  );
}
