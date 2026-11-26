"""API scenarios shared by two suites: in-memory (tests/api) and Postgres (tests/integration).

Subclasses provide the `env` fixture. These classes are not collected directly (no Test prefix).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from app.domain import TIP_COPY
from app.providers.fake_misc import RecordingEmail
from tests.support.api_env import ApiEnv
from tests.support.builders import PHOTO

PASSWORD = "correct-horse-1"
FORBIDDEN_KEYS = {"calories", "kcal", "macros", "grams", "weight", "height", "bmi", "score"}


def keys_of(value: Any) -> set[str]:
    if isinstance(value, dict):
        found = set(value)
        for item in value.values():
            found |= keys_of(item)
        return found
    if isinstance(value, list):
        return set().union(*(keys_of(item) for item in value)) if value else set()
    return set()


async def signup(
    env: ApiEnv, email: str = "ana@example.com", *, meal_consent: bool = True
) -> dict[str, str]:
    response = await env.client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "name": "Ana",
            "timezone": "America/Sao_Paulo",
            "adult_confirmed": True,
        },
    )
    assert response.status_code == 201, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    if meal_consent:
        consent = await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": True},
            headers=headers,
        )
        assert consent.status_code == 201, consent.text
    return headers


async def post_meal(
    env: ApiEnv,
    headers: dict[str, str],
    data: bytes = PHOTO,
    content_type: str = "image/jpeg",
) -> Any:
    return await env.client.post(
        "/v1/meals", files={"photo": ("meal.jpg", data, content_type)}, headers=headers
    )


NO_ATTRIBUTES = {"strength": 0, "speed": 0, "skill": 0, "endurance": 0, "intelligence": 0}


async def manual_meal(env: ApiEnv, headers: dict[str, str]) -> Any:
    response = await env.client.post(
        "/v1/meals/manual", json={"items": ["arroz"], "meal_type": "lunch"}, headers=headers
    )
    assert response.status_code == 201, response.text
    return response.json()


async def allocate(env: ApiEnv, headers: dict[str, str], body: object) -> Any:
    return await env.client.post("/v1/pet/attributes", json=body, headers=headers)


def assert_error(response: Any, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["message"]


class ApiCases:
    """Subclasses must define an async `env` fixture."""

    async def test_health(self, env: ApiEnv) -> None:
        assert (await env.client.get("/health")).json() == {"status": "ok"}
        ready = await env.client.get("/health/ready")
        assert ready.status_code == 200
        assert ready.json()["status"] == "ready"

    async def test_unknown_route_and_missing_token_use_error_envelope(self, env: ApiEnv) -> None:
        assert_error(await env.client.get("/v1/nope"), 404, "NOT_FOUND")
        assert_error(await env.client.get("/v1/pet"), 401, "UNAUTHORIZED")
        bad = await env.client.get("/v1/pet", headers={"Authorization": "Bearer garbage"})
        assert_error(bad, 401, "INVALID_TOKEN")

    async def test_register_login_refresh_and_me(self, env: ApiEnv) -> None:
        headers = await signup(env)
        me = (await env.client.get("/v1/me", headers=headers)).json()
        assert me["email"] == "ana@example.com"
        assert me["plan"] == "free"
        assert me["timezone"] == "America/Sao_Paulo"
        assert [c["type"] for c in me["consents"]] == ["meal_data"]
        assert "password" not in str(me)

        duplicate = await env.client.post(
            "/v1/auth/register",
            json={
                "email": "ANA@example.com",
                "password": PASSWORD,
                "name": "Ana",
                "adult_confirmed": True,
            },
        )
        assert_error(duplicate, 409, "EMAIL_ALREADY_REGISTERED")

        bad = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": "wrong-password"}
        )
        assert_error(bad, 401, "INVALID_CREDENTIALS")
        login = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        tokens = login.json()
        assert tokens["token_type"] == "bearer"

        refreshed = await env.client.post(
            "/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert refreshed.status_code == 200
        wrong_kind = await env.client.post(
            "/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
        )
        assert_error(wrong_kind, 401, "INVALID_TOKEN")

    async def test_register_requires_adult_and_valid_input(self, env: ApiEnv) -> None:
        minor = await env.client.post(
            "/v1/auth/register",
            json={
                "email": "kid@example.com",
                "password": PASSWORD,
                "name": "Kid",
                "adult_confirmed": False,
            },
        )
        assert_error(minor, 422, "ADULT_CONFIRMATION_REQUIRED")
        invalid = await env.client.post(
            "/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "short",
                "name": "",
                "adult_confirmed": True,
            },
        )
        assert_error(invalid, 422, "VALIDATION_ERROR")
        assert "short" not in invalid.text  # input values are never echoed
        bad_zone = await env.client.post(
            "/v1/auth/register",
            json={
                "email": "zone@example.com",
                "password": PASSWORD,
                "name": "Zed",
                "timezone": "Mars/Base",
                "adult_confirmed": True,
            },
        )
        assert_error(bad_zone, 422, "INVALID_TIMEZONE")

    async def test_forgot_password_answers_the_same_for_known_and_unknown_emails(
        self, env: ApiEnv
    ) -> None:
        await signup(env)
        known = await env.client.post("/v1/auth/password/forgot", json={"email": "ana@example.com"})
        unknown = await env.client.post(
            "/v1/auth/password/forgot", json={"email": "nobody@example.com"}
        )
        assert known.status_code == unknown.status_code == 202
        assert known.json() == unknown.json() == {"status": "accepted"}
        assert_error(
            await env.client.post("/v1/auth/password/forgot", json={"email": "nope"}),
            422,
            "VALIDATION_ERROR",
        )

    async def test_reset_password_with_emailed_token(self, env: ApiEnv) -> None:
        await signup(env)
        await env.client.post("/v1/auth/password/forgot", json={"email": "ana@example.com"})
        outbox = env.ctx.email
        assert isinstance(outbox, RecordingEmail)
        [(_, _, body)] = outbox.sent
        link = next(line for line in body.splitlines() if "token=" in line)
        token = parse_qs(urlparse(link.strip()).query)["token"][0]

        new_password = "brand-new-pass-2"
        short = await env.client.post(
            "/v1/auth/password/reset", json={"token": token, "password": "short"}
        )
        assert_error(short, 422, "VALIDATION_ERROR")
        done = await env.client.post(
            "/v1/auth/password/reset", json={"token": token, "password": new_password}
        )
        assert done.status_code == 204
        again = await env.client.post(
            "/v1/auth/password/reset", json={"token": token, "password": new_password}
        )
        assert_error(again, 400, "INVALID_RESET_TOKEN")
        login = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": new_password}
        )
        assert login.status_code == 200
        old = await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        assert_error(old, 401, "INVALID_CREDENTIALS")

    async def test_meal_endpoints_require_meal_consent(self, env: ApiEnv) -> None:
        headers = await signup(env, meal_consent=False)
        assert_error(await post_meal(env, headers), 403, "MEAL_CONSENT_REQUIRED")
        assert_error(
            await env.client.get("/v1/meals", headers=headers), 403, "MEAL_CONSENT_REQUIRED"
        )
        # Revoking after accepting blocks again.
        await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": True},
            headers=headers,
        )
        assert (await post_meal(env, headers)).status_code == 201
        await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": False},
            headers=headers,
        )
        assert_error(await post_meal(env, headers), 403, "MEAL_CONSENT_REQUIRED")

    async def test_log_meal_returns_meal_pet_and_events_without_forbidden_fields(
        self, env: ApiEnv
    ) -> None:
        headers = await signup(env)
        response = await post_meal(env, headers)
        assert response.status_code == 201, response.text
        body = response.json()
        assert set(body) == {"meal", "pet", "events", "pet_tip"}
        assert body["pet_tip"] is None  # Free plan: no "Seus hábitos" tip
        assert body["pet"]["points"] == 10
        assert body["pet"]["mood"] == "happy"
        assert body["pet"]["streak_days"] == 1
        assert body["events"] == []
        assert body["meal"]["source"] == "photo"
        assert not FORBIDDEN_KEYS & keys_of(body)

    async def test_premium_meal_gets_an_approved_pet_tip(self, env: ApiEnv) -> None:
        headers = await signup(env)
        await env.grant_premium(await env.user_id_for("ana@example.com"))
        body = (await post_meal(env, headers)).json()
        assert body["pet_tip"] in TIP_COPY.values()

    async def test_manual_meal_after_unreadable_photo(self, env: ApiEnv) -> None:
        headers = await signup(env)
        assert_error(await post_meal(env, headers, b""), 422, "PHOTO_NOT_READABLE")
        response = await env.client.post(
            "/v1/meals/manual",
            json={"items": ["arroz", "feijão"], "meal_type": "lunch"},
            headers=headers,
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert set(body) == {"meal", "pet", "events", "pet_tip"}
        assert body["meal"]["source"] == "manual"
        assert body["meal"]["items"] == ["arroz", "feijão"]
        assert body["meal"]["meal_type"] == "lunch"
        assert (body["pet"]["points"], body["pet"]["mood"]) == (10, "happy")
        assert not FORBIDDEN_KEYS & keys_of(body)
        meal_id = body["meal"]["id"]
        got = (await env.client.get(f"/v1/meals/{meal_id}", headers=headers)).json()
        assert got == body["meal"]
        # The AI photo limit is untouched: two photos still go through.
        assert (await post_meal(env, headers, b"one")).status_code == 201
        assert (await post_meal(env, headers, b"two")).status_code == 201
        assert_error(await post_meal(env, headers, b"three"), 429, "DAILY_LIMIT_REACHED")
        env.next_day()
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert (pet["lives"], pet["streak_days"]) == (2, 1)

    async def test_manual_meal_validation_and_consent(self, env: ApiEnv) -> None:
        headers = await signup(env, meal_consent=False)
        body = {"items": ["ovo"], "meal_type": "breakfast"}
        assert_error(
            await env.client.post("/v1/meals/manual", json=body, headers=headers),
            403,
            "MEAL_CONSENT_REQUIRED",
        )
        await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": True},
            headers=headers,
        )
        for bad in (
            {"items": [], "meal_type": "lunch"},
            {"items": ["   "], "meal_type": "lunch"},
            {"items": ["ovo"], "meal_type": "brunch"},
            {"items": ["ovo"], "meal_type": "lunch", "calories": 100},
        ):
            assert_error(
                await env.client.post("/v1/meals/manual", json=bad, headers=headers),
                422,
                "VALIDATION_ERROR",
            )
        assert_error(await env.client.post("/v1/meals/manual", json=body), 401, "UNAUTHORIZED")

    async def test_daily_limit_and_failed_analysis_do_not_cost_lives(self, env: ApiEnv) -> None:
        headers = await signup(env)
        assert_error(await post_meal(env, headers, b"NOTFOOD"), 422, "NOT_FOOD")
        assert_error(await post_meal(env, headers, b"UNAVAILABLE"), 503, "VISION_UNAVAILABLE")
        assert_error(await post_meal(env, headers, b""), 422, "PHOTO_NOT_READABLE")
        assert (await post_meal(env, headers, b"one")).status_code == 201
        assert (await post_meal(env, headers, b"two")).status_code == 201
        assert_error(await post_meal(env, headers, b"three"), 429, "DAILY_LIMIT_REACHED")
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert pet["lives"] == 2
        assert pet["points"] == 20

    async def test_photo_validation(self, env: ApiEnv) -> None:
        headers = await signup(env)
        not_image = await post_meal(env, headers, b"hello", "text/plain")
        assert_error(not_image, 422, "PHOTO_NOT_READABLE")
        too_big = await post_meal(env, headers, b"x" * (1024 * 1024 + 1))
        assert_error(too_big, 413, "PHOTO_TOO_LARGE")

    async def test_meal_crud(self, env: ApiEnv) -> None:
        headers = await signup(env)
        created = (await post_meal(env, headers)).json()["meal"]
        meal_id = created["id"]

        listed = (await env.client.get("/v1/meals?range=today", headers=headers)).json()
        assert [m["id"] for m in listed["items"]] == [meal_id]
        assert listed["next_cursor"] is None
        assert (await env.client.get(f"/v1/meals/{meal_id}", headers=headers)).json() == created

        patched = await env.client.patch(
            f"/v1/meals/{meal_id}",
            json={"items": ["tapioca", "egg"], "meal_type": "breakfast"},
            headers=headers,
        )
        assert patched.status_code == 200
        assert patched.json()["items"] == ["tapioca", "egg"]
        assert patched.json()["item_count"] == 2
        assert patched.json()["meal_type"] == "breakfast"

        assert (await env.client.delete(f"/v1/meals/{meal_id}", headers=headers)).status_code == 204
        assert_error(
            await env.client.get(f"/v1/meals/{meal_id}", headers=headers), 404, "MEAL_NOT_FOUND"
        )
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert pet["points"] == 10  # deleting never changes points

    async def test_meal_pagination_and_ranges(self, env: ApiEnv) -> None:
        headers = await signup(env)
        await post_meal(env, headers, b"a")
        await post_meal(env, headers, b"b")
        env.next_day()
        await post_meal(env, headers, b"c")
        today = (await env.client.get("/v1/meals?range=today", headers=headers)).json()
        assert len(today["items"]) == 1
        first = (await env.client.get("/v1/meals?range=7d&limit=2", headers=headers)).json()
        assert len(first["items"]) == 2
        assert first["next_cursor"]
        second = (
            await env.client.get(
                f"/v1/meals?range=7d&limit=2&cursor={first['next_cursor']}", headers=headers
            )
        ).json()
        assert len(second["items"]) == 1
        assert second["next_cursor"] is None
        bad = await env.client.get("/v1/meals?cursor=@@@", headers=headers)
        assert_error(bad, 422, "INVALID_CURSOR")

    async def test_meals_are_private_between_users(self, env: ApiEnv) -> None:
        ana = await signup(env, "ana@example.com")
        bob = await signup(env, "bob@example.com")
        meal_id = (await post_meal(env, ana)).json()["meal"]["id"]
        assert_error(
            await env.client.get(f"/v1/meals/{meal_id}", headers=bob), 404, "MEAL_NOT_FOUND"
        )
        assert_error(
            await env.client.delete(f"/v1/meals/{meal_id}", headers=bob), 404, "MEAL_NOT_FOUND"
        )

    async def test_pet_read_edit_and_lazy_fainting(self, env: ApiEnv) -> None:
        headers = await signup(env)
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert pet == {
            "name": None,  # unnamed until screen 43
            "color": "default",
            "lives": 2,
            "max_lives": 4,
            "streak_days": 0,
            "points": 0,
            "mood": "tired",
            "level": 1,
            "level_progress": {"points": 0, "current_level_at": 0, "next_level_at": 100},
            "attributes": NO_ATTRIBUTES,
            "unspent_attribute_points": 1,
            "events": [],
            "support_hint": False,
        }
        for bad_name in ("x" * 21, "", "   "):
            assert_error(
                await env.client.patch("/v1/pet", json={"name": bad_name}, headers=headers),
                422,
                "VALIDATION_ERROR",
            )
        assert (await env.client.get("/v1/pet", headers=headers)).json()["name"] is None
        named = await env.client.patch("/v1/pet", json={"name": "x" * 20}, headers=headers)
        assert named.json()["name"] == "x" * 20
        renamed = await env.client.patch(
            "/v1/pet", json={"name": "Pipoca", "color": "blue"}, headers=headers
        )
        assert renamed.json()["name"] == "Pipoca"
        assert renamed.json()["color"] == "blue"

        env.next_day(3)
        fainted = (await env.client.get("/v1/pet", headers=headers)).json()
        assert (fainted["lives"], fainted["mood"], fainted["events"]) == (
            0,
            "fainted",
            ["life_lost"],
        )
        assert (await env.client.get("/v1/pet", headers=headers)).json()["events"] == []
        woke = (await post_meal(env, headers)).json()
        assert woke["events"] == ["wake_up"]
        assert woke["pet"]["lives"] == 1
        assert woke["pet"]["points"] == 15

    async def test_pause_requires_premium(self, env: ApiEnv) -> None:
        headers = await signup(env)
        assert_error(
            await env.client.post("/v1/pet/pause", json={"days": 3}, headers=headers),
            402,
            "PREMIUM_REQUIRED",
        )
        await env.grant_premium(await env.user_id_for("ana@example.com"))
        assert_error(
            await env.client.post("/v1/pet/pause", json={"days": 2}, headers=headers),
            422,
            "VALIDATION_ERROR",
        )
        paused = await env.client.post("/v1/pet/pause", json={"days": 3}, headers=headers)
        assert paused.status_code == 200
        assert paused.json()["mood"] == "paused"
        assert_error(
            await env.client.post("/v1/pet/pause", json={"days": 1}, headers=headers),
            409,
            "PET_ALREADY_PAUSED",
        )
        env.next_day(2)
        assert (await env.client.get("/v1/pet", headers=headers)).json()["lives"] == 2
        resumed = await env.client.delete("/v1/pet/pause", headers=headers)
        assert resumed.status_code == 200
        assert resumed.json()["mood"] != "paused"
        assert_error(
            await env.client.delete("/v1/pet/pause", headers=headers), 409, "PET_NOT_PAUSED"
        )

    async def test_me_patch_export_and_pending_deletion(self, env: ApiEnv) -> None:
        headers = await signup(env)
        await post_meal(env, headers)
        patched = await env.client.patch(
            "/v1/me",
            json={"timezone": "America/New_York", "analytics_opt_out": True},
            headers=headers,
        )
        assert patched.json()["timezone"] == "America/New_York"
        assert patched.json()["analytics_opt_out"] is True
        assert_error(
            await env.client.patch("/v1/me", json={"timezone": "Nope/Zone"}, headers=headers),
            422,
            "INVALID_TIMEZONE",
        )

        exported = (await env.client.get("/v1/me/export", headers=headers)).json()
        assert len(exported["meals"]) == 1
        assert exported["points"][0]["amount"] == 10
        assert "password" not in str(exported)
        assert not FORBIDDEN_KEYS & keys_of(exported)

        deleted = await env.client.delete("/v1/me", headers=headers)
        assert deleted.status_code == 202
        assert deleted.json()["deletion_scheduled_for"] is not None
        # Signing in again cancels the pending deletion.
        await env.client.post(
            "/v1/auth/login", json={"email": "ana@example.com", "password": PASSWORD}
        )
        me = (await env.client.get("/v1/me", headers=headers)).json()
        assert me["deletion_scheduled_for"] is None

    async def test_consent_validation(self, env: ApiEnv) -> None:
        headers = await signup(env, meal_consent=False)
        bad = await env.client.post(
            "/v1/consents",
            json={"type": "unknown", "version": "1", "accepted": True},
            headers=headers,
        )
        assert_error(bad, 422, "VALIDATION_ERROR")

    async def test_level_up_event_and_spending_attribute_points(self, env: ApiEnv) -> None:
        headers = await signup(env)
        # 3 scored meals a day x 10 points: 90 points after three days, still level 1.
        for day in range(3):
            if day:
                env.next_day()
            for _ in range(3):
                body = await manual_meal(env, headers)
                assert "level_up" not in body["events"]
        assert (body["pet"]["points"], body["pet"]["level"]) == (90, 1)
        env.next_day()
        body = await manual_meal(env, headers)  # 100 points: level 2
        assert "level_up" in body["events"]
        assert body["pet"]["level"] == 2
        assert body["pet"]["level_progress"] == {
            "points": 100,
            "current_level_at": 100,
            "next_level_at": 200,
        }
        assert body["pet"]["unspent_attribute_points"] == 3  # 1 (level 1) + 2 (level 2)
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert "level_up" not in pet["events"]  # returned once

        spent = await allocate(env, headers, {"allocations": {"strength": 2, "skill": 1}})
        assert spent.status_code == 200, spent.text
        assert spent.json()["attributes"] == {**NO_ATTRIBUTES, "strength": 2, "skill": 1}
        assert spent.json()["unspent_attribute_points"] == 0
        assert_error(
            await allocate(env, headers, {"allocations": {"speed": 1}}),
            400,
            "NOT_ENOUGH_ATTRIBUTE_POINTS",
        )
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert pet["attributes"] == {**NO_ATTRIBUTES, "strength": 2, "skill": 1}

        env.next_day(3)  # fainted: level and attributes stay
        fainted = (await env.client.get("/v1/pet", headers=headers)).json()
        assert (fainted["lives"], fainted["level"]) == (0, 2)
        assert fainted["attributes"] == pet["attributes"]
        assert fainted["points"] == 100

    async def test_spending_more_than_unspent_changes_nothing(self, env: ApiEnv) -> None:
        headers = await signup(env, meal_consent=False)  # same gates as GET /pet
        assert_error(
            await allocate(env, headers, {"allocations": {"speed": 1, "endurance": 1}}),
            400,
            "NOT_ENOUGH_ATTRIBUTE_POINTS",
        )
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert (pet["attributes"], pet["unspent_attribute_points"]) == (NO_ATTRIBUTES, 1)
        ok = await allocate(env, headers, {"allocations": {"intelligence": 1}})
        assert ok.status_code == 200, ok.text
        assert ok.json()["attributes"]["intelligence"] == 1

    @pytest.mark.parametrize(
        "body",
        [
            {"allocations": {"luck": 1}},
            {"allocations": {"speed": 0}},
            {"allocations": {"speed": -1}},
            {"allocations": {"speed": 1.5}},
            {"allocations": {"speed": "1"}},
            {"allocations": {"speed": True}},
            {"allocations": {}},
            {},
            {"allocations": {"speed": 1}, "extra": 1},
        ],
    )
    async def test_attribute_allocation_validation(self, env: ApiEnv, body: object) -> None:
        headers = await signup(env)
        assert_error(await allocate(env, headers, body), 422, "VALIDATION_ERROR")
        pet = (await env.client.get("/v1/pet", headers=headers)).json()
        assert pet["unspent_attribute_points"] == 1

    async def test_attribute_allocation_needs_auth(self, env: ApiEnv) -> None:
        response = await env.client.post("/v1/pet/attributes", json={"allocations": {"speed": 1}})
        assert_error(response, 401, "UNAUTHORIZED")

    @pytest.mark.parametrize("path", ["/v1/me", "/v1/pet", "/v1/meals", "/v1/me/export"])
    async def test_protected_routes_need_auth(self, env: ApiEnv, path: str) -> None:
        assert_error(await env.client.get(path), 401, "UNAUTHORIZED")


class ConsentRevocationCases:
    """Revocation and delete-all-meals over HTTP. Subclass with an `env` fixture."""

    async def test_revoke_meal_data_returns_403_and_follow_ups(self, env: ApiEnv) -> None:
        headers = await signup(env)
        assert (await post_meal(env, headers)).status_code == 201
        revoked = await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": False},
            headers=headers,
        )
        assert revoked.status_code == 201
        assert revoked.json()["suggested_actions"] == ["export", "delete_meals", "delete_account"]
        assert_error(await post_meal(env, headers), 403, "MEAL_CONSENT_REQUIRED")
        assert_error(
            await env.client.get("/v1/meals", headers=headers), 403, "MEAL_CONSENT_REQUIRED"
        )
        assert (await env.client.get("/v1/me/export", headers=headers)).status_code == 200
        pet = await env.client.get("/v1/pet", headers=headers)
        assert pet.status_code == 200
        assert pet.json()["support_hint"] is False

    async def test_delete_all_meals_keeps_pet(self, env: ApiEnv) -> None:
        headers = await signup(env)
        await post_meal(env, headers)
        await env.client.post(
            "/v1/consents",
            json={"type": "meal_data", "version": "1.0", "accepted": False},
            headers=headers,
        )
        deleted = await env.client.delete("/v1/meals", headers=headers)
        assert deleted.status_code == 200
        assert deleted.json() == {"deleted": 1}
        export = await env.client.get("/v1/me/export", headers=headers)
        assert export.json()["meals"] == []
        pet = await env.client.get("/v1/pet", headers=headers)
        assert pet.json()["points"] == 10
        assert_error(await env.client.delete("/v1/meals"), 401, "UNAUTHORIZED")
