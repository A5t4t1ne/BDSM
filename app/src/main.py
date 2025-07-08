from website import create_app
import json
import os

app = create_app()


if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(path, 'config.json')

    with open(fpath, 'r') as f:
        run = json.load(f)['run']

    app.run(debug=run['debug'], host=run['host'], port=run['port'])