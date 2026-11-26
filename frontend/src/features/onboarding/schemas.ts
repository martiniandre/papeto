import { z } from 'zod';

/** docs/api.md: PATCH /pet name <= 20 chars. */
export const PET_NAME_MAX = 20;

export const petNameSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'onboarding.name.required')
    .max(PET_NAME_MAX, 'onboarding.name.tooLong'),
});

export type PetNameValues = z.infer<typeof petNameSchema>;
