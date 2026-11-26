"""API scenarios for push tokens and notification preferences, shared by the in-memory and
Postgres suites. Subclasses provide the `env` fixture."""

from __future__ import annotations

from tests.api_cases import assert_error, signup
from tests.support.api_env import ApiEnv

TOKEN = "ExponentPushToken[abcDEF123_-xyz]"
OTHER_TOKEN = "ExpoPushToken[second-device-1]"


async def _tokens_of(env: ApiEnv, email: str) -> list[tuple[str, str]]:
    user_id = await env.user_id_for(email)
    async with env.ctx.uow_factory() as uow:
        return [(t.token, t.platform) for t in await uow.push_tokens.list_for_user(user_id)]


class PushTokenCases:
    async def test_register_and_refresh_token(self, env: ApiEnv) -> None:
        headers = await signup(env)
        first = await env.client.post(
            "/v1/push-tokens", json={"token": TOKEN, "platform": "ios"}, headers=headers
        )
        assert first.status_code == 201, first.text
        assert first.json() == {"token": TOKEN, "platform": "ios"}
        again = await env.client.post(
            "/v1/push-tokens", json={"token": TOKEN, "platform": "android"}, headers=headers
        )
        assert again.status_code == 201
        assert await _tokens_of(env, "ana@example.com") == [(TOKEN, "android")]

    async def test_token_moves_to_the_last_user_that_registers_it(self, env: ApiEnv) -> None:
        ana = await signup(env, "ana@example.com")
        bia = await signup(env, "bia@example.com")
        for headers in (ana, bia):
            response = await env.client.post(
                "/v1/push-tokens", json={"token": TOKEN, "platform": "ios"}, headers=headers
            )
            assert response.status_code == 201
        assert await _tokens_of(env, "ana@example.com") == []
        assert await _tokens_of(env, "bia@example.com") == [(TOKEN, "ios")]

    async def test_delete_token_is_scoped_to_its_owner_and_idempotent(self, env: ApiEnv) -> None:
        ana = await signup(env, "ana@example.com")
        bia = await signup(env, "bia@example.com")
        await env.client.post(
            "/v1/push-tokens", json={"token": TOKEN, "platform": "ios"}, headers=ana
        )
        # Another user cannot remove it.
        assert (await env.client.delete(f"/v1/push-tokens/{TOKEN}", headers=bia)).status_code == 204
        assert await _tokens_of(env, "ana@example.com") == [(TOKEN, "ios")]
        assert (await env.client.delete(f"/v1/push-tokens/{TOKEN}", headers=ana)).status_code == 204
        assert (await env.client.delete(f"/v1/push-tokens/{TOKEN}", headers=ana)).status_code == 204
        assert await _tokens_of(env, "ana@example.com") == []

    async def test_push_tokens_need_no_meal_consent(self, env: ApiEnv) -> None:
        headers = await signup(env, meal_consent=False)
        response = await env.client.post(
            "/v1/push-tokens", json={"token": OTHER_TOKEN, "platform": "android"}, headers=headers
        )
        assert response.status_code == 201

    async def test_invalid_token_or_platform_is_rejected(self, env: ApiEnv) -> None:
        headers = await signup(env)
        for body in (
            {"token": "not-an-expo-token", "platform": "ios"},
            {"token": TOKEN, "platform": "windows"},
            {"token": TOKEN},
            {"token": TOKEN, "platform": "ios", "extra": 1},
        ):
            response = await env.client.post("/v1/push-tokens", json=body, headers=headers)
            assert_error(response, 422, "VALIDATION_ERROR")

    async def test_push_tokens_require_authentication(self, env: ApiEnv) -> None:
        post = await env.client.post("/v1/push-tokens", json={"token": TOKEN, "platform": "ios"})
        assert_error(post, 401, "UNAUTHORIZED")
        assert_error(await env.client.delete(f"/v1/push-tokens/{TOKEN}"), 401, "UNAUTHORIZED")
