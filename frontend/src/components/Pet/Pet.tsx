import { useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, View } from 'react-native';
import { useTranslation } from 'react-i18next';

import type { Mood, PetEvent } from '@/api/types';
import { useReduceMotion } from '@/hooks/useReduceMotion';
import { cn } from '@/utils/cn';

import { celebratingArt, moodArt } from './art';

export interface PetProps {
  mood: Mood;
  /** One-shot events from the API (`celebrate`, `wake_up`, `life_lost`, `level_up`). */
  events?: readonly PetEvent[];
  name: string;
  size?: number;
  className?: string;
}

const CELEBRATION_MS = 2500;

/** Events that play the one-shot celebration art. */
const hasCelebrationEvent = (events: readonly PetEvent[]) =>
  events.some((event) => event === 'celebrate' || event === 'wake_up' || event === 'level_up');

/**
 * Renders what the API says: the app never computes the mood.
 * Later this becomes the Rive state machine `Pet` (inputs: mood, celebrate, lifeLost, wakeUp, reduceMotion).
 * With reduce motion on, the image is static and one-shot animations are skipped (events are still announced).
 */
export function Pet({ mood, events = [], name, size = 220, className }: PetProps) {
  const { t } = useTranslation();
  const reduceMotion = useReduceMotion();
  const [breathe] = useState(() => new Animated.Value(0));
  // Key of the events whose celebration already finished (derived state: no setState in the effect body).
  const [finishedKey, setFinishedKey] = useState('');
  const eventsKey = events.join(',');
  const hasCelebration = hasCelebrationEvent(events);

  // Announce and play one-shot events.
  useEffect(() => {
    if (!eventsKey) return;
    const list = eventsKey.split(',') as PetEvent[];
    for (const event of list) {
      AccessibilityInfo.announceForAccessibility(t(`pet.events.${event}`, { name }));
    }
    if (reduceMotion) return;
    if (hasCelebrationEvent(list)) {
      const timer = setTimeout(() => setFinishedKey(eventsKey), CELEBRATION_MS);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [eventsKey, name, reduceMotion, t]);

  // Idle "breathing" loop; disabled for reduce motion.
  useEffect(() => {
    if (reduceMotion || mood === 'fainted') {
      breathe.setValue(0);
      return;
    }
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(breathe, {
          toValue: 1,
          duration: 1600,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(breathe, {
          toValue: 0,
          duration: 1600,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [breathe, mood, reduceMotion]);

  const showCelebration = hasCelebration && finishedKey !== eventsKey && !reduceMotion;
  const scale = breathe.interpolate({ inputRange: [0, 1], outputRange: [1, 1.03] });

  return (
    <View
      testID="pet"
      accessible
      accessibilityRole="image"
      accessibilityLabel={t('pet.a11y', { name, mood: t(`pet.mood.${mood}`) })}
      className={cn('items-center justify-center', className)}
    >
      <Animated.Image
        testID={showCelebration ? 'pet-art-celebrate' : `pet-art-${mood}`}
        source={showCelebration ? celebratingArt : moodArt[mood]}
        resizeMode="contain"
        style={{
          width: size,
          height: size,
          transform: reduceMotion ? [] : [{ scale }],
        }}
      />
    </View>
  );
}
