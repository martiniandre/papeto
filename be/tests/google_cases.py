"""Google sign-in and adult confirmation scenarios shared by the in-memory and Postgres suites.

Subclasses provide the `env` fixture. Not collected directly (no Test prefix).
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from app.services.retention import purge_deleted_accounts
from tests.api_cases import PASSWORD, signup
from tests.support.api_env import ApiEnv

SUB = "google-sub-123"
TOKEN_KEYS = {"access_token", "refresh_token", "token_type", "expires_in", "is_new_user"}


def bearer(body: dict[str, Any]) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['access_token']}"}


async def google_sign_in(
    env: ApiEnv,
    *,
    subject: str = SUB,
    email: str = "ana@example.com",
    timezone: str | None = None,
    **claims: Any,
) -> Any:
    token = env.google.issue(subject=subject, email=email, now=env.clock.now(), **claims)
    body: dict[str, str] = {"id_token": token}
    if timezone is not None:
        body["timezone"] = timezone
    return await env.client.post("/v1/auth/google", json=body)


def error_code(response: Any) -> str:
    code: str = response.json()["error"]["code"]
    return code


class GoogleSignInCases:
    async def test_new_user_is_created_without_adult_confirmation(self, env: ApiEnv) -> None:
        response = await google_sign_in(env, name="Ana Google", timezone="America/Manaus")
        assert response.status_code == 200, response.text
        body = response.json()
        assert set(body) == TOKEN_KEYS
        assert body["is_new_user"] is True
        assert body["token_type"] == "bearer"
        me = (await env.client.get("/v1/me", headers=bearer(body))).json()
        assert me["adult_confirmed"] is False
        assert me["timezone"] == "America/Manaus"
        assert me["email"] == "ana@example.com"
        assert me["name"] == "Ana Google"

    async def test_default_timezone_and_repeat_sign_in(self, env: ApiEnv) -> None:
        first = (await google_sign_in(env)).json()
        again = await google_sign_in(env)
        assert again.status_code == 200
        assert again.json()["is_new_user"] is False
        me_first = (await env.client.get("/v1/me", headers=bearer(first))).json()
        me_again = (await env.client.get("/v1/me", headers=bearer(again.json()))).json()
        assert me_first["id"] == me_again["id"]
        assert me_first["timezone"] == "America/Sao_Paulo"

    async def test_invalid_timezone_is_rejected(self, env: ApiEnv) -> None:
        response = await google_sign_in(env, timezone="Mars/Olympus")
        assert response.status_code == 422
        assert error_code(response) == "INVALID_TIMEZONE"

    async def test_existing_email_account_is_linked(self, env: ApiEnv) -> None:
        headers = await signup(env, "ana@example.com")
        user_id = (await env.client.get("/v1/me", headers=headers)).json()["id"]

        response = await google_sign_in(env, email="ANA@Example.com")
        assert response.status_code == 200, response.text
        assert response.json()["is_new_user"] is False
        me = (await env.client.get("/v1/me", headers=bearer(response.json()))).json()
        assert me["id"] == user_id
        assert me["adult_confirmed"] is True  # confirmed at email sign-up

        # Linked by subject now, so a changed Google email still finds the same account.
        moved = await google_sign_in(env, email="ana.new@example.com")
        assert moved.json()["is_new_user"] is False
        me = (await env.client.get("/v1/me", headers=bearer(moved.json()))).json()
        assert me["id"] == user_id

        login = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        assert login.status_code == 200  # the password still works

        export = (await env.client.get("/v1/me/export", headers=headers)).json()
        assert export["user"]["auth_provider"] == "email"
        assert export["user"]["google_subject"] == SUB

    async def test_google_only_account_has_no_password(self, env: ApiEnv) -> None:
        await google_sign_in(env)
        login = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        assert login.status_code == 401
        assert error_code(login) == "INVALID_CREDENTIALS"

    async def test_pending_deletion_is_cancelled_for_a_linked_account(self, env: ApiEnv) -> None:
        headers = await signup(env, "ana@example.com")
        assert (await env.client.delete("/v1/me", headers=headers)).status_code == 202
        response = await google_sign_in(env)
        assert response.status_code == 200
        me = (await env.client.get("/v1/me", headers=bearer(response.json()))).json()
        assert me["deletion_scheduled_for"] is None

    async def test_pending_deletion_is_cancelled_for_a_google_account(self, env: ApiEnv) -> None:
        first = (await google_sign_in(env)).json()
        assert (await env.client.delete("/v1/me", headers=bearer(first))).status_code == 202
        env.next_day(10)
        again = await google_sign_in(env)
        assert again.json()["is_new_user"] is False
        me = (await env.client.get("/v1/me", headers=bearer(again.json()))).json()
        assert me["deletion_scheduled_for"] is None

    async def test_anonymized_account_signs_up_fresh(self, env: ApiEnv) -> None:
        first = (await google_sign_in(env)).json()
        old_id = (await env.client.get("/v1/me", headers=bearer(first))).json()["id"]
        await env.client.delete("/v1/me", headers=bearer(first))
        env.next_day(31)
        await purge_deleted_accounts(env.ctx)
        again = await google_sign_in(env)
        assert again.status_code == 200
        assert again.json()["is_new_user"] is True
        me = (await env.client.get("/v1/me", headers=bearer(again.json()))).json()
        assert me["id"] != old_id

    async def test_token_errors(self, env: ApiEnv) -> None:
        cases: list[tuple[dict[str, Any], int, str]] = [
            ({"audience": "someone-else"}, 401, "GOOGLE_TOKEN_INVALID"),
            ({"issuer": "https://evil.example"}, 401, "GOOGLE_TOKEN_INVALID"),
            ({"ttl": timedelta(seconds=-1)}, 401, "GOOGLE_TOKEN_INVALID"),
            ({"email_verified": False}, 401, "GOOGLE_EMAIL_NOT_VERIFIED"),
        ]
        for claims, status, code in cases:
            response = await google_sign_in(env, **claims)
            assert response.status_code == status, claims
            assert error_code(response) == code, claims
        garbage = await env.client.post("/v1/auth/google", json={"id_token": "garbage"})
        assert garbage.status_code == 401
        assert error_code(garbage) == "GOOGLE_TOKEN_INVALID"
        missing = await env.client.post("/v1/auth/google", json={})
        assert missing.status_code == 422
        assert error_code(missing) == "VALIDATION_ERROR"

    async def test_jwks_outage_is_503(self, env: ApiEnv) -> None:
        env.google.available = False
        response = await google_sign_in(env)
        assert response.status_code == 503
        assert error_code(response) == "AUTH_PROVIDER_UNAVAILABLE"

    async def test_failed_sign_in_creates_nothing(self, env: ApiEnv) -> None:
        await google_sign_in(env, email_verified=False)
        async with env.ctx.uow_factory() as uow:
            assert await uow.users.get_by_email("ana@example.com") is None


class AdultConfirmationCases:
    async def test_pet_and_meals_need_adult_confirmation(self, env: ApiEnv) -> None:
        headers = bearer((await google_sign_in(env)).json())
        consent = await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": True},
            headers=headers,
        )
        assert consent.status_code == 201  # consents are recorded on the same screen

        blocked = [
            await env.client.get("/v1/pet", headers=headers),
            await env.client.patch("/v1/pet", json={"name": "Bolinha"}, headers=headers),
            await env.client.post("/v1/pet/pause", json={"days": 1}, headers=headers),
            await env.client.delete("/v1/pet/pause", headers=headers),
            await env.client.get("/v1/meals", headers=headers),
            await env.client.post(
                "/v1/meals/manual",
                json={"items": ["arroz"], "meal_type": "lunch"},
                headers=headers,
            ),
            await env.client.post(
                "/v1/meals",
                files={"photo": ("p.jpg", b"\xff\xd8\xff fake", "image/jpeg")},
                headers=headers,
            ),
        ]
        for response in blocked:
            assert response.status_code == 403, (response.request.url, response.text)
            assert error_code(response) == "ADULT_CONFIRMATION_REQUIRED"

    async def test_export_and_deletion_always_work(self, env: ApiEnv) -> None:
        headers = bearer((await google_sign_in(env)).json())
        export = await env.client.get("/v1/me/export", headers=headers)
        assert export.status_code == 200
        assert export.json()["user"]["adult_confirmed_at"] is None
        assert export.json()["user"]["auth_provider"] == "google"
        assert (await env.client.delete("/v1/meals", headers=headers)).status_code == 200
        assert (await env.client.delete("/v1/me", headers=headers)).status_code == 202

    async def test_confirming_unlocks_pet_and_is_kept_once(self, env: ApiEnv) -> None:
        headers = bearer((await google_sign_in(env)).json())
        patched = await env.client.patch("/v1/me", json={"adult_confirmed": True}, headers=headers)
        assert patched.status_code == 200
        assert patched.json()["adult_confirmed"] is True
        first = (await env.client.get("/v1/me/export", headers=headers)).json()
        confirmed_at = first["user"]["adult_confirmed_at"]
        assert confirmed_at is not None

        env.next_day()
        await env.client.patch("/v1/me", json={"adult_confirmed": True}, headers=headers)
        later = (await env.client.get("/v1/me/export", headers=headers)).json()
        assert later["user"]["adult_confirmed_at"] == confirmed_at

        pet = await env.client.get("/v1/pet", headers=headers)
        assert pet.status_code == 200
        assert pet.json()["name"] is None

    async def test_only_true_is_accepted(self, env: ApiEnv) -> None:
        headers = bearer((await google_sign_in(env)).json())
        for value in (False, None, "yes"):
            response = await env.client.patch(
                "/v1/me", json={"adult_confirmed": value}, headers=headers
            )
            if value is None:
                assert response.status_code == 200  # field omitted in effect: nothing changes
                assert response.json()["adult_confirmed"] is False
            else:
                assert response.status_code == 422, value
                assert error_code(response) == "VALIDATION_ERROR"

    async def test_register_without_confirmation_is_still_422(self, env: ApiEnv) -> None:
        response = await env.client.post(
            "/v1/auth/register",
            json={
                "email": "bia@example.com",
                "password": PASSWORD,
                "name": "Bia",
                "adult_confirmed": False,
            },
        )
        assert response.status_code == 422
        assert error_code(response) == "ADULT_CONFIRMATION_REQUIRED"

    async def test_email_users_are_confirmed_already(self, env: ApiEnv) -> None:
        headers = await signup(env, "bia@example.com")
        me = (await env.client.get("/v1/me", headers=headers)).json()
        assert me["adult_confirmed"] is True
        assert (await env.client.get("/v1/pet", headers=headers)).status_code == 200
