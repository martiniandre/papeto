import { Stack } from 'expo-router';

import { colors } from '@/theme/tokens';

/** Flow 4: notifications (27), export data (36), delete account (35), pushed from Profile. */
export default function AccountLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    />
  );
}
