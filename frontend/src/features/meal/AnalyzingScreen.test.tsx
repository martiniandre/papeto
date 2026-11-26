import { onlineManager } from '@tanstack/react-query';
import { act } from '@testing-library/react-native';
import { router } from 'expo-router';

import { ApiError, NETWORK_ERROR } from '@/api/client';
import { api } from '@/api/endpoints';
import { useMealFlowStore } from '@/stores/mealFlow';
import { renderWithProviders } from '@/test/render';

import AnalyzingScreen from './AnalyzingScreen';
import { discardPhoto } from './photo';

jest.mock('@/api/endpoints', () => ({ api: { createMeal: jest.fn() } }));
jest.mock('./photo', () => ({ discardPhoto: jest.fn() }));

describe('<AnalyzingScreen /> offline queue', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    onlineManager.setOnline(true);
    useMealFlowStore.getState().reset();
  });

  it('keeps the photo in memory and opens the offline error when the request cannot reach the server', async () => {
    (api.createMeal as jest.Mock).mockRejectedValue(new ApiError(0, NETWORK_ERROR, ''));
    useMealFlowStore.getState().setPhoto('file:///cache/p.jpg');
    await renderWithProviders(<AnalyzingScreen />);
    await act(async () => {});
    expect(useMealFlowStore.getState().pendingPhotoUri).toBe('file:///cache/p.jpg');
    expect(discardPhoto).not.toHaveBeenCalled();
    expect(router.replace).toHaveBeenCalledWith({ pathname: '/meal/error', params: { reason: 'offline' } });
  });

  it('does not even call the API while the device is offline', async () => {
    onlineManager.setOnline(false);
    useMealFlowStore.getState().setPhoto('file:///cache/p.jpg');
    await renderWithProviders(<AnalyzingScreen />);
    await act(async () => {});
    expect(api.createMeal).not.toHaveBeenCalled();
    expect(useMealFlowStore.getState().pendingPhotoUri).toBe('file:///cache/p.jpg');
    expect(router.replace).toHaveBeenCalledWith({ pathname: '/meal/error', params: { reason: 'offline' } });
  });

  it('still discards the photo on other failures', async () => {
    (api.createMeal as jest.Mock).mockRejectedValue(new ApiError(422, 'NOT_FOOD', ''));
    useMealFlowStore.getState().setPhoto('file:///cache/p.jpg');
    await renderWithProviders(<AnalyzingScreen />);
    await act(async () => {});
    expect(discardPhoto).toHaveBeenCalledWith('file:///cache/p.jpg');
    expect(useMealFlowStore.getState().pendingPhotoUri).toBeNull();
  });
});
