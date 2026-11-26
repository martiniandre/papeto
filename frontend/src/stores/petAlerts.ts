import { create } from 'zustand';

/**
 * Bridges the one-shot `life_lost` event (GET /pet returns it once) to the screen that shows it.
 * The app only remembers that the API said so; it never computes lives or mood.
 */
interface PetAlertState {
  lifeLostPending: boolean;
  /** The fainted screen is shown once per faint, not on every Home visit. */
  faintedShown: boolean;
  noteLifeLost: () => void;
  clearLifeLost: () => void;
  setFaintedShown: (shown: boolean) => void;
}

export const usePetAlertStore = create<PetAlertState>((set) => ({
  lifeLostPending: false,
  faintedShown: false,
  noteLifeLost: () => set({ lifeLostPending: true }),
  clearLifeLost: () => set({ lifeLostPending: false }),
  setFaintedShown: (faintedShown) => set({ faintedShown }),
}));
