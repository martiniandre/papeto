import { useCallback, useMemo } from 'react';

/**
 * AuthPort-style boundary for Google sign-in. Screens depend on this hook only, so tests mock it and
 * the native library never leaks into UI code.
 *
 * The native module does not exist in Expo Go, so it is loaded lazily inside try/catch: in Expo Go
 * `available` is false and the screen shows a friendly "not available in this version" state.
 */
export type GoogleSignInFailure = 'cancelled' | 'unavailable' | 'failed';

export class GoogleSignInError extends Error {
  readonly reason: GoogleSignInFailure;
  constructor(reason: GoogleSignInFailure) {
    super(reason);
    this.name = 'GoogleSignInError';
    this.reason = reason;
  }
}

export interface GoogleSignInPort {
  /** False when the native module is missing (Expo Go) or no client id is configured. */
  available: boolean;
  /** Opens the Google account picker and resolves with the id token. Rejects with GoogleSignInError. */
  signIn: () => Promise<string>;
}

type NativeModule = typeof import('@react-native-google-signin/google-signin');

let native: NativeModule | null | undefined;
let configured = false;

function loadNative(): NativeModule | null {
  if (native !== undefined) return native;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    native = require('@react-native-google-signin/google-signin') as NativeModule;
    // Touch the native side so a missing module throws here and not on press.
    void native.GoogleSignin;
  } catch {
    native = null;
  }
  return native;
}

const webClientId = process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID;
const iosClientId = process.env.EXPO_PUBLIC_GOOGLE_IOS_CLIENT_ID;

function ensureConfigured(module: NativeModule): void {
  if (configured) return;
  // The web client id makes Google issue an id token whose audience the backend verifies.
  module.GoogleSignin.configure({ webClientId, iosClientId });
  configured = true;
}

export function useGoogleSignIn(): GoogleSignInPort {
  const available = useMemo(() => Boolean(webClientId) && loadNative() !== null, []);

  const signIn = useCallback(async (): Promise<string> => {
    const module = loadNative();
    if (!webClientId || !module) throw new GoogleSignInError('unavailable');
    try {
      ensureConfigured(module);
      await module.GoogleSignin.hasPlayServices({ showPlayServicesUpdateDialog: true });
      const response = await module.GoogleSignin.signIn();
      if (response.type !== 'success') throw new GoogleSignInError('cancelled');
      if (!response.data.idToken) throw new GoogleSignInError('failed');
      return response.data.idToken;
    } catch (error) {
      if (error instanceof GoogleSignInError) throw error;
      if (module.isErrorWithCode(error)) {
        if (error.code === module.statusCodes.SIGN_IN_CANCELLED) {
          throw new GoogleSignInError('cancelled');
        }
        if (error.code === module.statusCodes.PLAY_SERVICES_NOT_AVAILABLE) {
          throw new GoogleSignInError('unavailable');
        }
      }
      throw new GoogleSignInError('failed');
    }
  }, []);

  return { available, signIn };
}
