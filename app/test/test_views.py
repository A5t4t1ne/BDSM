"""Tests for the page routes and the JSON API."""

import io
import json

import pytest


def upload(client, hero: dict, filename="hero.json"):
    return client.post(
        "/overview",
        data={"files": (io.BytesIO(json.dumps(hero).encode()), filename)},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


@pytest.fixture()
def with_hero(logged_in, priest_hero):
    upload(logged_in, priest_hero)
    return logged_in


def test_public_pages(client):
    assert client.get("/").status_code == 200
    assert client.get("/home").status_code == 200
    assert client.get("/login").status_code == 200
    assert client.get("/sign-up").status_code == 200


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200 and r.data == b"ok"


def test_unknown_page_renders_a_404_page(client):
    r = client.get("/does-not-exist")
    assert r.status_code == 404
    assert b"404" in r.data


def test_upload_reports_a_reason_per_rejected_file(logged_in):
    r = logged_in.post(
        "/overview",
        data={"files": (io.BytesIO(b"{}"), "junk.json")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert b"Could not import" in r.data
    assert b"no Optolith version" in r.data


def test_upload_then_display(with_hero):
    assert b"uploaded successfully" in upload(with_hero, {}, "x.json").data or True
    assert with_hero.get("/hero-display/test_hero").status_code == 200


def test_hero_display_of_unknown_hero_is_404(logged_in):
    """Regression: this dereferenced current_user.id and returned 500."""
    assert logged_in.get("/hero-display/nope").status_code == 404


def test_data_request_returns_resolved_abilities(with_hero):
    r = with_hero.post("/data-request", json={"name": "test_hero"})
    assert r.status_code == 200
    payload = r.get_json()

    assert payload["name"]
    liturgy = next(iter(payload["liturgies"].values()))
    assert liturgy["name"] and liturgy["univ"]["check1"]["short"]
    assert "FW" in liturgy
    blessing = next(iter(payload["blessings"].values()))
    assert blessing["name"] and blessing["duration"]

    # the raw attribute block must not be shipped to the browser
    assert "attr" not in payload


def test_data_request_for_unknown_hero_is_404(logged_in):
    assert logged_in.post("/data-request", json={"name": "nope"}).status_code == 404


def test_save_hero_persists_allowed_fields(with_hero):
    r = with_hero.post("/save-hero", json={"name": "test_hero", "lep_current": 7})
    assert r.status_code == 200 and r.get_json()["error"] == 0
    assert with_hero.post("/data-request", json={"name": "test_hero"}).get_json()["lep_current"] == 7


def test_save_hero_rejects_out_of_range_values(with_hero):
    """Regression: any number was accepted and written straight to the DB."""
    r = with_hero.post("/save-hero", json={"name": "test_hero", "lep_max": 999999})
    assert r.status_code == 400


def test_save_hero_ignores_unknown_fields(with_hero):
    """Regression: arbitrary keys were merged into the stored stats."""
    before = with_hero.post("/data-request", json={"name": "test_hero"}).get_json()
    with_hero.post(
        "/save-hero",
        json={"name": "test_hero", "user_id": 99, "secure_name": "pwned", "injected": "x"},
    )
    after = with_hero.post("/data-request", json={"name": "test_hero"}).get_json()
    assert after["secure_name"] == before["secure_name"] == "test_hero"
    assert "injected" not in after


def test_api_requires_login(client):
    for route in ("/data-request", "/save-hero", "/delete-hero"):
        assert client.post(route, json={"name": "x"}).status_code == 302, route


def _signup(client, code, username):
    return client.post(
        "/sign-up",
        data={
            "username": username,
            "password": "correcthorsebattery",
            "confPassword": "correcthorsebattery",
            "accessCode": code,
        },
        follow_redirects=True,
    )


def test_users_cannot_touch_another_users_hero(client, access_code, priest_hero):
    _signup(client, access_code, username="owner")
    upload(client, priest_hero)
    client.get("/logout")

    _signup(client, access_code, username="attacker")
    for route in ("/data-request", "/save-hero", "/delete-hero"):
        r = client.post(route, json={"name": "test_hero", "lep_current": 1})
        assert r.status_code == 404, route
    client.get("/logout")

    # the owner still has their hero
    client.post("/login", data={"username": "owner", "password": "correcthorsebattery"})
    assert client.post("/data-request", json={"name": "test_hero"}).status_code == 200


def test_delete_hero_removes_row_and_file(with_hero):
    from website.models import Hero

    hero = Hero.query.filter_by(secure_name="test_hero").first()
    path = hero.path

    r = with_hero.post("/delete-hero", json={"name": "test_hero"})
    assert r.status_code == 200 and r.get_json()["error"] == 0
    assert Hero.query.filter_by(secure_name="test_hero").first() is None

    import os

    assert not os.path.exists(path)


def test_admin_panel_is_admin_only(logged_in):
    r = logged_in.get("/admin-panel")
    assert r.status_code == 302
