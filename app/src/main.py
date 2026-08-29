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
    path = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(path, "config.json")

    with open(fpath, "r") as f:
        run = json.load(f)["run"]

    app.run(debug=run["debug"], host=run["host"], port=run["port"])
