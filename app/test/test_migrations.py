"""Schema bootstrap: fresh, restarted, adopted, and started concurrently."""

import multiprocessing as mp
import os
import sqlite3
from pathlib import Path


def _dirs(tmp_path):
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    secrets = tmp_path / "secrets"
    secrets.mkdir(exist_ok=True)
    (secrets / "secret_key").write_text("test-secret-key")
    (secrets / "access_code").write_text("test-access-code")
    (secrets / "admin_pw").write_text("test-admin-password")
    return data, secrets


def _boot(data: str, secrets: str, uploads: str, result=None):
    """Build an app in this process, as a gunicorn worker would."""
    os.environ.update(
        BDSM_DATA_DIR=data,
        BDSM_SECRETS_DIR=secrets,
        BDSM_UPLOAD_DIR=uploads,
        BDSM_INSECURE_COOKIES="1",
    )
    import importlib

    import website

    importlib.reload(website)
    try:
        website.create_app()
        if result is not None:
            result.put(("ok", None))
    except Exception as e:  # pragma: no cover - only on regression
        if result is not None:
            result.put(("fail", f"{type(e).__name__}: {e}"))
        else:
            raise


def _tables(data: Path) -> set[str]:
    con = sqlite3.connect(data / "database.db")
    try:
        return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        con.close()


def test_fresh_database_gets_every_table(tmp_path):
    data, secrets = _dirs(tmp_path)
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    ctx = mp.get_context("spawn")
    p = ctx.Process(target=_boot, args=(str(data), str(secrets), str(uploads)))
    p.start()
    p.join(120)
    assert p.exitcode == 0

    assert {"user", "hero", "friendship", "campaign", "campaign_membership", "alembic_version"} <= _tables(data)


def test_concurrent_workers_do_not_race(tmp_path):
    """Regression: four gunicorn workers each ran the migrations at once, and
    the losers died with "table ... already exists", taking the app down on
    every cold start."""
    data, secrets = _dirs(tmp_path)
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    ctx = mp.get_context("spawn")
    result = ctx.Queue()
    workers = [
        ctx.Process(target=_boot, args=(str(data), str(secrets), str(uploads), result))
        for _ in range(4)
    ]
    for w in workers:
        w.start()
    for w in workers:
        w.join(180)

    outcomes = [result.get() for _ in workers]
    failures = [msg for status, msg in outcomes if status != "ok"]
    assert not failures, f"workers failed to boot: {failures}"
    assert all(w.exitcode == 0 for w in workers)
    assert "campaign" in _tables(data)


def test_restart_is_a_noop(tmp_path):
    data, secrets = _dirs(tmp_path)
    uploads = tmp_path / "uploads"
    uploads.mkdir()

    ctx = mp.get_context("spawn")
    for _ in range(2):
        p = ctx.Process(target=_boot, args=(str(data), str(secrets), str(uploads)))
        p.start()
        p.join(120)
        assert p.exitcode == 0

    con = sqlite3.connect(data / "database.db")
    try:
        # exactly one admin, and one revision row
        assert con.execute("SELECT count(*) FROM user WHERE username='admin'").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM alembic_version").fetchone()[0] == 1
    finally:
        con.close()
