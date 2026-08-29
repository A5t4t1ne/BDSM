# Change log

## 0.3.0

### Fix

-   App did not start: `constants.py` crashed on import, taking `create_app()` with it
-   Imports referenced a `src` package that does not exist inside the container
-   Hero upload failed: the decoder returned a model the uploader still treated as a dict
-   Reference models did not match the shipped data, so nothing validated
-   Heroes without Improved Dodge crashed the decoder
-   The "reduced encumbrance" rule never applied, because it was looked up in the wrong place
-   Resolving abilities wrote into the shared reference tables, leaking one hero's
    skill levels into later requests
-   The play screen showed `undefined` for initiative and could not render special abilities
-   The test suite collected nothing

### Security

-   Passwords must be at least 12 characters; an empty password was previously accepted
-   Login and sign-up are rate limited, and unknown usernames no longer answer faster
-   Session and remember cookies are `HttpOnly`, `Secure` and `SameSite=Lax`
-   `/hero-display` required no login and returned 500 to anonymous visitors
-   `/save-hero` accepted arbitrary fields and values; it now takes a validated allowlist
-   A crafted hero file could inject script into the play screen
-   TLS private keys are no longer baked into the nginx image
-   Added HSTS, a self-only CSP, and `client_max_body_size` matching the app's upload limit
-   The admin password is no longer reset from the secret on every restart

### Features

-   Change your password from the account page
-   Uploads say why a file was rejected
-   Database migrations, applied automatically at startup

### Miscellaneous

-   `create_app()` is a real application factory
-   SQLite runs in WAL mode with a busy timeout, so workers stop blocking each other
-   Bootstrap is served locally; the app needs no internet access
-   Reproducible builds from `uv.lock`; CI runs lint, tests, an image build and a boot probe
-   README documents setup, local development and the environment variables

## 0.2.2

### Fix

-   Assemble details not working

## 0.2.1

### Features

-   Cantrips are now loaded

### Miscellaneous

-   Text details are no longer stored in database but assembled before sending to client

## 0.2.0

### Features

-   More hero stats are now visible in the play tab
    -   Hero liturgies
    -   Hero spells

### Enhancements

-   Added all current official effects
-   Changing money now adjusts automatically if value goes below 0.

### Miscellaneous

-   Hero files are now saved in Optolith-standard json file format
-   Added simple admin panel
-   Added user role level

### Security

-   Added CSRF protection

## 0.1.0

First release

### Features

-   First version of the project
    -   User creation
    -   Hero opload
    -   Basic hero stats tracking
