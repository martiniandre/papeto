import { File, Paths } from 'expo-file-system';
import { ImageManipulator, SaveFormat } from 'expo-image-manipulator';

/** Longest side sent to the API (frontend/AGENTS.md). */
export const MAX_PHOTO_SIDE = 1024;

export interface CapturedPhoto {
  uri: string;
  width: number;
  height: number;
}

/** Target size keeping the aspect ratio, or null when the photo is already small enough. */
export function resizeTarget(
  width: number,
  height: number,
  max = MAX_PHOTO_SIDE,
): { width: number } | { height: number } | null {
  if (Math.max(width, height) <= max) return null;
  return width >= height ? { width: max } : { height: max };
}

/**
 * Resizes to max 1024 px on the longest side and re-encodes as JPEG into the app cache.
 * The caller must `discardPhoto` both the original and the resized file after the upload.
 * Photos are never written to the gallery.
 */
export async function resizePhoto(photo: CapturedPhoto): Promise<string> {
  const context = ImageManipulator.manipulate(photo.uri);
  const target = resizeTarget(photo.width, photo.height);
  if (target) context.resize(target);
  const image = await context.renderAsync();
  try {
    const result = await image.saveAsync({ compress: 0.8, format: SaveFormat.JPEG });
    return result.uri;
  } finally {
    image.release();
    context.release();
  }
}

/** Deletes a temporary photo file. Only touches files inside the app cache (never the gallery). */
export function discardPhoto(uri: string | null | undefined): void {
  if (!uri) return;
  try {
    if (!uri.startsWith(Paths.cache.uri)) return;
    const file = new File(uri);
    if (file.exists) file.delete();
  } catch {
    // Best effort: the OS clears the cache directory anyway. Never log the URI.
  }
}
