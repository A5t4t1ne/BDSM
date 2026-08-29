# BDSM

Of course it stands for: **_Browser DSA Stat Manager_** and nothing else you horny guys.  
The goal is to create a cross-platform application for keeping track of your hero stats
in the german pen & paper game [Das schwarze
Auge](https://ulisses-spiele.de/game-system/das-schwarze-auge/) from [Ulisses
Spiele](https://ulisses-spiele.de/).

## Running it

You need Docker and an Optolith hero export (`.json`) to play with.

### 1. Create the secrets

Three secret files are read at startup and are never committed:

```sh
mkdir -p app/secrets && chmod 700 app/secrets
openssl rand -hex 32 > app/secrets/secret_key.txt    # signs sessions
openssl rand -hex 16 > app/secrets/access_code.txt   # required to sign up
printf 'pick-a-real-password' > app/secrets/admin_pw.txt
```

`admin_pw.txt` seeds the `admin` account the first time the database is
created. It is *not* re-applied on later starts, so change the password in the
app rather than in the file. To force a reset from the file, start once with
`BDSM_RESET_ADMIN=1`.

### 2. TLS certificates

nginx expects a certificate at `nginx/letsencrypt/live/<domain>/`. The
directory is bind-mounted, not baked into the image, so certificates can be
renewed without rebuilding. For a local run you can self-sign:

```sh
mkdir -p nginx/letsencrypt/live/hans.li
openssl req -x509 -newkey rsa:2048 -days 365 -nodes \
  -keyout nginx/letsencrypt/live/hans.li/privkey.pem \
  -out nginx/letsencrypt/live/hans.li/fullchain.pem -subj "/CN=localhost"
```

### 3. Start

```sh
docker compose up --build
```

The app is then on <http://localhost:8080> and <https://localhost:4443>.
Sign up with the access code from step 1, then upload a hero on the Overview
page.

### Exporting a hero from Optolith

In [Optolith](https://github.com/elyukai/optolith-client), open your hero and
choose **Save as JSON** from the hero menu. Exports from Optolith 1.0 or newer
are accepted; the upload page names the reason if a file is rejected.

## Friends and campaigns

Add someone as a friend by their exact username; they confirm the request from
their own Friends page. Nothing is shared automatically yet -- the friend list
is what later features will build on.

A campaign groups players together. Whoever creates one is its game master and
is the only person who can invite or remove members. Invitees see the campaign
before they accept, so they know what they are joining, and can decline. The
owner deletes a campaign rather than leaving it, so it is never left without a
game master.

Roles live in `CampaignRole` and membership state in `MembershipStatus`, so a
future feature (shared notes, session logs, a hero roster per campaign) should
hang off `CampaignMembership` or a new table rather than needing changes here.


## Development

```sh
cd app
uv sync                      # install dependencies from uv.lock
uv run pytest                # run the test suite
uv run ruff check src/ test/ # lint
```

To run the app outside Docker, point it at local directories:

```sh
export BDSM_DATA_DIR=/tmp/bdsm-data BDSM_SECRETS_DIR="$PWD/secrets" \
       BDSM_INSECURE_COOKIES=1
mkdir -p "$BDSM_DATA_DIR"
cd src && uv run python main.py
```

Secrets can also come from `BDSM_SECRET_KEY`, `BDSM_ACCESS_CODE` and
`BDSM_ADMIN_PW` instead of files. `BDSM_INSECURE_COOKIES=1` drops the `Secure`
flag so a plain-HTTP dev run can hold a session -- never set it in production.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `BDSM_DATA_DIR` | `/data` | SQLite database and log file |
| `BDSM_SECRETS_DIR` | `/run/secrets` | Where the secret files are read from |
| `BDSM_INSECURE_COOKIES` | unset | `1` drops the `Secure` cookie flag (dev only) |
| `BDSM_RESET_ADMIN` | unset | `1` resets the admin password from the secret |
| `BDSM_RATELIMIT_STORAGE` | `memory://` | A `redis://` URI shares login rate limits across workers |
| `BDSM_LOG_LEVEL` | `INFO` | loguru level |

### Database migrations

The schema is managed with Flask-Migrate and upgraded automatically at startup.
After changing a model:

```sh
cd app/src
FLASK_APP="website:create_app" uv run flask db migrate -m "what changed"
```

Review the generated file in `src/migrations/versions/` before committing it.

### Reference data

`app/src/website/data/*.json` is the DSA reference data the app reads at
runtime. `app/Data/` holds the upstream Optolith YAML it is derived from, in
several locales; nothing reads it at runtime and it is excluded from the image.


## Improvement

Feedback or suggestions are very welcome, please open an issue - or even better: a pull request!

## Note

I'm just a random dude who was asked by some friends to do this, so don't have high
expectations regarding the software architecture.

And yes. There are no bugs. Only features. Even if the data is not updated properly in the database.

## Credits

The initial idea comes from the C# Application [DELM](https://github.com/Ducttapemummy/DELM).  
And of course the project would not be possible without:

- The contributors to the [Optolith Project](https://github.com/elyukai/optolith-client).
- The playmaker [Ulisses Spiele](https://ulisses-spiele.de/).
