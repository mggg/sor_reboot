# SOR Reboot

Repo for the Some Other Race Reboot project.

## Setup

Run the following command to set up the project:

```bash
uv sync --locked
```

and then create an environment file by copying the example:

```bash
cp .env.example .env
```

you will need to fill in the `CENSUS_API_KEY` in the `.env` file with your own API key. This key
[https://api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html).
is available at
