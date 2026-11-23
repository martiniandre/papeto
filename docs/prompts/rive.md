# Rive prompt (Bolinha animations)

Prerequisite: Bolinha as an SVG with separate named parts, imported into an artboard `Bolinha` (512x512):

```
body, belly, ear_left, ear_right, eye_left, eye_right, eyelid_left, eyelid_right,
mouth_happy, mouth_neutral, mouth_sad, mouth_open, cheek_left, cheek_right,
arm_left, arm_right, foot_left, foot_right, shadow, nightcap, zzz, sparkles
```

Paste into the Rive AI agent with the file open:

```
You are animating "Bolinha", the mascot of a habit app. The artboard "Bolinha" (512x512) already contains the character as vector parts named: body, belly, ear_left, ear_right, eye_left, eye_right, eyelid_left, eyelid_right, mouth_happy, mouth_neutral, mouth_sad, mouth_open, cheek_left, cheek_right, arm_left, arm_right, foot_left, foot_right, shadow, nightcap, zzz, sparkles. Do not redraw or recolor anything; only animate.

1. Rig: add a root bone at the feet and a bone chain from body to head. Bind ears and arms to their own bones so they can rotate around their base.

2. Create these looping timelines (soft, cute, cartoon motion, ease in-out, never jerky):
- happy_idle (2.4s): gentle bounce of 6px, ears wiggle 4 degrees, blink every 2.4s (eyelids close for 0.12s), mouth_happy visible, cheeks pulse opacity 80-100%.
- tired_idle (3.2s): slower breathing (body scaleY 1.00-1.02), ears droop 12 degrees, eyelids half closed, mouth_neutral visible, no bounce.
- sleepy_idle (4s): eyelids almost closed, head tilts 6 degrees side to side, mouth_sad visible, one slow yawn using mouth_open at 2s.
- fainted_idle (3s): body lying down (rotate 80 degrees around the root bone), eyes hidden behind closed eyelids, small zzz floating up and fading, shadow flattened.
- paused_idle (4s): nightcap visible, eyes closed, calm breathing, zzz floating up and fading.

3. Create these one-shot timelines:
- celebrate (1.2s): squash 0.9 then stretch 1.1, jump 40px, arms up, mouth_open, sparkles scale from 0 to 1 and fade out, land with a small squash.
- life_lost (1.0s): small flinch backwards, ears drop fast then settle, mouth_sad, a short head shake.
- wake_up (1.4s): from fainted pose, rotate back up to standing with a little overshoot, eyelids open, blink twice, end in the happy_idle start pose.

4. Data binding: create a view model "PetVM" with an enum property "mood" (happy, tired, sleepy, fainted, paused), triggers "celebrate", "lifeLost", "wakeUp", and a boolean "reduceMotion".

5. State machine "Pet":
- Layer "Mood": one state per looping timeline, selected by PetVM.mood. Blend between mood states over 0.3s.
- Layer "Events": an empty Idle state; on each trigger, play the matching one-shot, then return to Idle. wakeUp is only allowed when mood is fainted and must end by setting the visual state to happy.
- When reduceMotion is true, every mood state shows its first frame only (no loop), and the one-shots are replaced by a 0.2s fade.

6. Keep it light for mobile: no blur effects, no more than 2 bones per limb, all motion on transform properties where possible. Name everything in English, exactly as written above.
```
