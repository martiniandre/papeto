import { ABORTED, ApiError, NETWORK_ERROR, request, setAdultConfirmationListener, setUnauthorizedListener } from './client';
import { tokenStorage } from './tokenStorage';

const json = (status: number, body: unknown) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }) as Response;

describe('api client', () => {
  const fetchMock = jest.fn();

  beforeEach(async () => {
    fetchMock.mockReset();
    global.fetch = fetchMock as unknown as typeof fetch;
    await tokenStorage.set({ access_token: 'access-1', refresh_token: 'refresh-1' });
  });

  it('calls /v1 with the bearer token', async () => {
    fetchMock.mockResolvedValueOnce(json(200, { name: 'Bolinha' }));
    await expect(request('/pet')).resolves.toEqual({ name: 'Bolinha' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8000/v1/pet');
    expect(init.headers.Authorization).toBe('Bearer access-1');
  });

  it('encodes query params and skips undefined ones', async () => {
    fetchMock.mockResolvedValueOnce(json(200, { items: [], next_cursor: null }));
    await request('/meals', { query: { range: '7d', cursor: undefined } });
    expect(fetchMock.mock.calls[0][0]).toBe('http://localhost:8000/v1/meals?range=7d');
  });

  it('turns the error envelope into an ApiError with the stable code', async () => {
    fetchMock.mockResolvedValueOnce(
      json(429, { error: { code: 'DAILY_LIMIT_REACHED', message: 'limit' } }),
    );
    await expect(request('/meals', { method: 'POST' })).rejects.toMatchObject({
      status: 429,
      code: 'DAILY_LIMIT_REACHED',
    });
  });

  it('refreshes once on 401 and retries with the new token', async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { error: { code: 'UNAUTHORIZED', message: '' } }))
      .mockResolvedValueOnce(json(200, { access_token: 'access-2', refresh_token: 'refresh-2' }))
      .mockResolvedValueOnce(json(200, { ok: true }));
    await expect(request('/me')).resolves.toEqual({ ok: true });
    expect(fetchMock.mock.calls[1][0]).toBe('http://localhost:8000/v1/auth/refresh');
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ refresh_token: 'refresh-1' });
    expect(fetchMock.mock.calls[2][1].headers.Authorization).toBe('Bearer access-2');
  });

  it('signs out when the refresh fails', async () => {
    const listener = jest.fn();
    setUnauthorizedListener(listener);
    fetchMock
      .mockResolvedValueOnce(json(401, { error: { code: 'UNAUTHORIZED', message: '' } }))
      .mockResolvedValueOnce(json(401, {}));
    await expect(request('/me')).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalled();
    await expect(tokenStorage.get()).resolves.toBeNull();
    setUnauthorizedListener(null);
  });

  it('reports network failures and aborts with client codes', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('Network request failed'));
    await expect(request('/pet')).rejects.toMatchObject({ code: NETWORK_ERROR });

    const controller = new AbortController();
    controller.abort();
    fetchMock.mockRejectedValueOnce(new Error('Aborted'));
    await expect(request('/meals', { signal: controller.signal })).rejects.toMatchObject({
      code: ABORTED,
    });
  });

  it('notifies the listener on 403 ADULT_CONFIRMATION_REQUIRED and still throws', async () => {
    const listener = jest.fn();
    setAdultConfirmationListener(listener);
    fetchMock.mockResolvedValueOnce(
      json(403, { error: { code: 'ADULT_CONFIRMATION_REQUIRED', message: '' } }),
    );
    await expect(request('/pet')).rejects.toMatchObject({ code: 'ADULT_CONFIRMATION_REQUIRED' });
    expect(listener).toHaveBeenCalledTimes(1);

    fetchMock.mockResolvedValueOnce(
      json(403, { error: { code: 'MEAL_CONSENT_REQUIRED', message: '' } }),
    );
    await expect(request('/meals')).rejects.toMatchObject({ code: 'MEAL_CONSENT_REQUIRED' });
    expect(listener).toHaveBeenCalledTimes(1);
    setAdultConfirmationListener(null);
  });
});
