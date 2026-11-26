import { create } from 'zustand';

export type SessionStatus = 'unknown' | 'signedOut' | 'signedIn';

interface SessionState {
  /** Whether tokens exist in secure storage. The tokens themselves never live here. */
  status: SessionStatus;
  setStatus: (status: SessionStatus) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  status: 'unknown',
  setStatus: (status) => set({ status }),
}));
