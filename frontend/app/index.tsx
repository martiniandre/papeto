import { Redirect } from 'expo-router';

import { useMe, usePet } from '@/api/queries';
import { ErrorState } from '@/components/ErrorState';
import { Screen } from '@/components/Screen';
import { Skeleton } from '@/components/Skeleton';
import { nextOnboardingRoute } from '@/features/onboarding/nextRoute';
import { useSessionStore } from '@/stores/session';

/** Entry: decides between Sign in, the remaining onboarding step, or Home. */
export default function Index() {
  const status = useSessionStore((state) => state.status);
  const signedIn = status === 'signedIn';
  const me = useMe(signedIn);
  const pet = usePet(signedIn);

  if (!signedIn) return <Redirect href="/(onboarding)/sign-in" />;
  if (me.isError || pet.isError) {
    return (
      <Screen>
        <ErrorState
          error={me.error ?? pet.error}
          onRetry={() => {
            void me.refetch();
            void pet.refetch();
          }}
        />
      </Screen>
    );
  }
  if (!me.data || !pet.data) {
    return (
      <Screen>
        <Skeleton hero />
      </Screen>
    );
  }
  return <Redirect href={nextOnboardingRoute(me.data, pet.data)} />;
}
