import { File } from 'expo-file-system';
import { ImageManipulator } from 'expo-image-manipulator';

import { discardPhoto, MAX_PHOTO_SIDE, resizePhoto, resizeTarget } from './photo';

jest.mock('expo-image-manipulator', () => {
  const image = {
    saveAsync: jest.fn(async () => ({ uri: 'file:///cache/resized.jpg', width: 1024, height: 768 })),
    release: jest.fn(),
  };
  const context = {
    resize: jest.fn(),
    renderAsync: jest.fn(async () => image),
    release: jest.fn(),
  };
  return {
    ImageManipulator: { manipulate: jest.fn(() => context) },
    SaveFormat: { JPEG: 'jpeg' },
    __context: context,
  };
});

jest.mock('expo-file-system', () => {
  const remove = jest.fn();
  return {
    Paths: { cache: { uri: 'file:///cache/' } },
    File: jest.fn().mockImplementation(() => ({ exists: true, delete: remove })),
    __remove: remove,
  };
});

const manipulatorMock = jest.requireMock('expo-image-manipulator') as {
  __context: { resize: jest.Mock };
};
const fsMock = jest.requireMock('expo-file-system') as { __remove: jest.Mock };

describe('resizeTarget', () => {
  it('limits the longest side to 1024 px', () => {
    expect(MAX_PHOTO_SIDE).toBe(1024);
    expect(resizeTarget(4032, 3024)).toEqual({ width: 1024 });
    expect(resizeTarget(3024, 4032)).toEqual({ height: 1024 });
  });

  it('does not upscale small photos', () => {
    expect(resizeTarget(800, 600)).toBeNull();
    expect(resizeTarget(1024, 1024)).toBeNull();
  });
});

describe('resizePhoto', () => {
  beforeEach(() => jest.clearAllMocks());

  it('resizes large photos and saves a JPEG in the cache', async () => {
    const uri = await resizePhoto({ uri: 'file:///cache/raw.jpg', width: 4000, height: 3000 });
    expect(ImageManipulator.manipulate).toHaveBeenCalledWith('file:///cache/raw.jpg');
    expect(manipulatorMock.__context.resize).toHaveBeenCalledWith({ width: 1024 });
    expect(uri).toBe('file:///cache/resized.jpg');
  });

  it('skips resize for small photos', async () => {
    await resizePhoto({ uri: 'file:///cache/raw.jpg', width: 640, height: 480 });
    expect(manipulatorMock.__context.resize).not.toHaveBeenCalled();
  });
});

describe('discardPhoto', () => {
  beforeEach(() => jest.clearAllMocks());

  it('deletes temporary files in the app cache', () => {
    discardPhoto('file:///cache/resized.jpg');
    expect(File).toHaveBeenCalledWith('file:///cache/resized.jpg');
    expect(fsMock.__remove).toHaveBeenCalled();
  });

  it('never touches files outside the cache (e.g. the gallery)', () => {
    discardPhoto('content://media/external/images/1');
    discardPhoto(null);
    expect(fsMock.__remove).not.toHaveBeenCalled();
  });
});
