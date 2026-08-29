import json
import os
import sys

from loguru import logger

from website import create_app

logger.remove()
logger.add(sys.stderr, level=os.environ.get("BDSM_LOG_LEVEL", "INFO"))
# enqueue=True routes writes through a single queue, so the four gunicorn
# workers cannot interleave or rotate the file on top of each other
logger.add(
    "/data/flask.log",
    rotation="5 MB",
    retention="10 days",
    level=os.environ.get("BDSM_LOG_LEVEL", "INFO"),
    enqueue=True,
)

app = create_app()

if __name__ == "__main__":
    # Local development entry point. config.json is optional; the defaults and
    # the BDSM_* environment variables cover a plain `python main.py` run.
    fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    run = {"debug": False, "host": "127.0.0.1", "port": 5000}

    if os.path.isfile(fpath):
        with open(fpath, "r", encoding="utf8") as f:
            run.update(json.load(f).get("run", {}))

    app.run(
        debug=os.environ.get("BDSM_DEBUG", str(run["debug"])).lower() in ("1", "true"),
        host=os.environ.get("BDSM_HOST", run["host"]),
        port=int(os.environ.get("BDSM_PORT", run["port"])),
    )
