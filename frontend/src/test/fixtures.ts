import type { Meal, Pet } from '@/api/types';

export const makeMeal = (overrides: Partial<Meal> = {}): Meal => ({
  id: 'm1',
  logged_at: new Date().toISOString(),
  local_day: '2026-01-01',
  meal_type: 'lunch',
  description: 'Um prato colorido com arroz, feijão e salada.',
  items: ['Arroz', 'Feijão', 'Salada'],
  food_groups: ['grains', 'legumes'],
  item_count: 3,
  colors: ['branco', 'marrom', 'verde'],
  confidence: 0.9,
  plate_share: {},
  new_foods: [],
  source: 'photo',
  ...overrides,
});

export const makePet = (overrides: Partial<Pet> = {}): Pet => ({
  name: 'Pipoca',
  color: 'mint',
  lives: 2,
  max_lives: 4,
  streak_days: 3,
  points: 40,
  mood: 'tired',
  events: [],
  support_hint: false,
  ...overrides,
});
