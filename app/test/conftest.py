import json
from pathlib import Path

import pytest

RESOURCES = Path(__file__).parent / "resources"


@pytest.fixture()
def app(tmp_path, monkeypatch):
    """A configured app backed by a throwaway data dir and secrets."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    secrets_dir = tmp_path / "secrets"
    secrets_dir.mkdir()
    (secrets_dir / "secret_key").write_text("test-secret-key")
    (secrets_dir / "access_code").write_text("test-access-code")
    (secrets_dir / "admin_pw").write_text("test-admin-password")

    monkeypatch.setenv("BDSM_DATA_DIR", str(data_dir))
    monkeypatch.setenv("BDSM_SECRETS_DIR", str(secrets_dir))
    monkeypatch.setenv("BDSM_INSECURE_COOKIES", "1")

    import website

    # the module-level Flask app is a singleton, so point the config that
    # create_app reads at this test's directories
    monkeypatch.setattr(website, "DATA_DIR", data_dir)
    monkeypatch.setattr(website, "SECRETS_DIR", secrets_dir)

    app = website.create_app(db_name="test.db", upload_folder=tmp_path / "heroes")
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        RATELIMIT_ENABLED=False,
    )

    # an active context lets tests query the models directly
    ctx = app.app_context()
    ctx.push()

    yield app

    website.db.session.remove()
    website.db.drop_all()
    ctx.pop()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


@pytest.fixture()
def access_code(app):
    return app.config["ACCESS_CODE"]


@pytest.fixture()
def logged_in(client, access_code):
    """A registered, logged-in client."""
    client.post(
        "/sign-up",
        data={
            "username": "testuser",
            "password": "correcthorsebattery",
            "confPassword": "correcthorsebattery",
            "accessCode": access_code,
        },
        follow_redirects=True,
    )
    return client


@pytest.fixture()
def priest_hero() -> dict:
    return json.loads((RESOURCES / "test_priest_hero.json").read_text(encoding="utf8"))


@pytest.fixture()
def magician_hero() -> dict:
    return json.loads((RESOURCES / "test_magician_hero.json").read_text(encoding="utf8"))
