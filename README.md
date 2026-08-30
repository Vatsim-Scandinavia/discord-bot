# VATSIM Scandinavia Discord Bot

The Discord bot for VATSIM Scandinavia. It verifies members against VATSIM and the Control Center, keeps roles in sync, runs event staffing threads, and maintains the server's standing messages.

Created by [Markus N.](https://github.com/Marko259) (1401513), [Daniel L.](https://github.com/blt950) (1352906), and [Thor H.](https://github.com/thor) (1512667).

Open sourced for contributions. Read the license before you copy any of the code.

## What the bot does

**Membership and roles**

- Grants and revokes the subdivision member role based on the VATSIM member list, using the CID in the member's nickname. The global VATSIM Community bot does the verification, this bot reads the result.
- Syncs mentor, buddy, examiner, training staff, visiting controller, and training roles from the [Control Center][control-center], including FIR specific variants.
- Assigns roles when members react to a message, so they can opt in to a FIR or a topic themselves.

**Events and staffing**

- Crossposts everything sent in the events channel, so members in other servers see it.
- Creates and updates staffing messages together with [the event system][events], driven by an HTTP API the event system calls.
- Lets controllers book and unbook positions with slash commands.

**Server upkeep**

- Prefixes the nickname of a member in a voice channel with their online VATSIM station, and restores the original nickname when they go offline.
- Posts and updates the rules, welcome, roles, and notification messages from Markdown files in `messages/`.
- Answers common questions about ATC applications, visiting, and waiting times when it detects them in chat.
- Provides METAR lookups and a few small admin commands.

## Prerequisites

- Python 3.14
- [uv](https://docs.astral.sh/uv/)
- [mise](https://mise.jdx.dev/) (optional, it runs the lint and test tasks)
- A Discord application with a bot token

In the Discord developer portal, turn on the **Server Members Intent**, the **Message Content Intent**, and the **Presence Intent**. In your server, give the bot role permission to manage roles and nicknames, and place it above every role it needs to assign.

## Set up the bot

1. Clone the repository.
2. Copy the example configuration and fill it in. No setting should be empty when you are done.

   ```bash
   cp .env.example .env
   ```

3. Install the dependencies.

   ```bash
   uv sync
   ```

4. Start the bot.

   ```bash
   uv run bot.py
   ```

To run it with a preset development port, use `mise run dev` instead.

### Run with Docker

The repository ships a Dockerfile and a Compose file. Build and start the bot with:

```bash
docker compose up -d --build
```

Prebuilt images are published to `ghcr.io/vatsim-scandinavia/discord-bot`.

## Configuration

All configuration comes from environment variables, loaded from `.env` at startup. `.env.example` lists every option. The most important ones are below.

### Connections

| Setting | Description |
| --- | --- |
| `BOT_TOKEN` | Your Discord bot token. |
| `GUILD_ID` | The ID of your Discord server. |
| `DEBUG` | Set to `True` in development. It switches logging to console format and skips the recurring jobs, which you can then start manually with the slash commands. |
| `VATSIM_API_TOKEN` | Token for the VATSIM API. |
| `VATSIM_CHECK_MEMBER_URL` | The VATSIM member list for your subdivision, for example `https://api.vatsim.net/api/subdivisions/SCA/members/?paginated`. |
| `VATSIM_SUBDIVISION` | The short code of your subdivision, for example `SCA`. |
| `DIVISION_URL` | The full URL to your homepage, for example `https://vatsim-scandinavia.org`. |
| `CC_API_URL`, `CC_API_TOKEN` | The [Control Center][control-center] API connection. |
| `EVENT_CALENDAR_URL`, `EVENT_API_TOKEN` | The [event system][events] API connection. |
| `SENTRY_KEY` | Sentry DSN. Sentry is only enabled when `DEBUG` is off. |
| `CACHE_DIR` | Where the bot stores its nickname cache. Defaults to `/var/cache/discord-bot`. |

### HTTP API

The bot runs a small FastAPI server so the event system can push staffing updates to it.

| Setting | Description |
| --- | --- |
| `FASTAPI_URL` | The address to bind to. Defaults to `127.0.0.1`. |
| `FASTAPI_PORT` | The port to bind to. Defaults to `80`. |
| `FASTAPI_TOKEN` | A bearer token that callers must send. Generate a UUID. |

Two endpoints are available, both `POST` and both authenticated with the bearer token:

- `/staffings/setup` posts a new staffing message and pins it. Form field: `id`.
- `/staffings/update` refreshes an existing staffing message. Form fields: `id`, and optionally `reset`.

### Channels and roles

Channel IDs: `EVENTS_CHANNEL`, `RULES_CHANNEL`, `WELCOME_CHANNEL`, `ROLES_CHANNEL`.

Role IDs:

| Setting | Description |
| --- | --- |
| `VATSCA_MEMBER_ROLE` | The subdivision member role that the bot manages. |
| `VATSIM_MEMBER_ROLE` | The role set by the VATSIM Community bot. The bot uses it as a gate. |
| `MENTOR_ROLE`, `BUDDY_ROLE`, `TRAINING_STAFF_ROLE`, `VISITOR_ROLE` | Roles assigned from Control Center data. |
| `OBS_ROLE` | Used to check who may book staffing positions. |

Which Control Center role names map to which Discord role is configurable, so you can use your own naming. Matching is case insensitive, and you can list several names separated by commas.

```
CC_MENTOR_ROLES='mentor'
CC_BUDDY_ROLES='buddy'
CC_TRAINING_ROLES='moderator'
```

### FIR specific roles

Several settings map a role to a FIR. They all use the format `FIR:role_id`, with entries separated by commas.

| Setting | Description |
| --- | --- |
| `FIR_DATA` | Mentor role per FIR. |
| `BUDDY_DATA` | Buddy role per FIR. |
| `EXAMINER_DATA` | Examiner role per FIR. |
| `CONTROLLER_FIR_DATA` | Controller role per FIR. |

```
FIR_DATA=Denmark:1234567890,Norway:1234567891,Sweden:1234567892
```

`RATING_FIR_DATA` and `TRAINING_DATA` add a rating to the mapping. Separate the FIR from its ratings with `|`, and separate FIRs with `,`.

```
RATING_FIR_DATA=Denmark|S1:1234567890|S2:1234567891,Norway|S3:1234567892
TRAINING_DATA=Denmark|S2:1234567890,Norway|S1:1234567891
```

A rating that is missing from `TRAINING_DATA` is neither granted nor cleaned up by the bot.

### Reaction roles

`REACTION_ROLE_DATA` uses the format `:emoji_name:|message_id|role_id`, with entries separated by commas.

```
REACTION_ROLE_DATA=:calendar:|1234567890|0987654321,:airplane:|1234567890|1234509876
```

The same emoji can point to different roles on different messages, because the bot matches on the message and emoji together.

**Emoji names must match what the `emoji` library produces at runtime.** The name you see in Discord may differ from the one the bot uses internally, and a mismatch means the reaction is ignored without an error. To find the right name, run:

```bash
uv run python -c "import emoji; print(emoji.demojize('🌍'))"
```

Replace 🌍 with your emoji and use the output, for example `:globe_showing_Europe-Africa:`.

**Message IDs must match real messages the bot has posted.** After the bot creates the reaction role messages, right click each one in Discord, select *Copy Message ID*, update `REACTION_ROLE_DATA`, and restart the bot.

### Intervals

Interval settings are in seconds. Set a positive value, because `0` makes the loop run without pausing.

| Setting | Description |
| --- | --- |
| `CHECK_MEMBERS_INTERVAL` | How often to check every member against the VATSIM member list. Defaults to 86400. |
| `STAFFING_INTERVAL` | How often the recurring slash command sync runs. |

### Station prefix

| Setting | Description |
| --- | --- |
| `STATION_PREFIX_CALLSIGN_SEPARATOR` | The character between the station and the nickname. Defaults to `\|`. |
| `STATION_PREFIX_SHOW_PILOTS` | Whether pilots also get a prefix. Defaults to `True`. |

## Slash commands

Most commands are limited to the staff roles listed in `helpers/config.py`.

| Command | Who can use it | What it does |
| --- | --- | --- |
| `/metar <airport>` | Everyone | Shows the METAR for an airport. |
| `/book`, `/unbook` | Members without the observer role | Books or releases a position in a staffing. |
| `/refreshevent`, `/manreset` | Staff | Refreshes or resets a staffing message. |
| `/checkusers` | Staff | Runs the membership check now. |
| `/checkroles` | Staff | Runs the Control Center role sync now. |
| `/sync` | Staff | Syncs slash commands with Discord. |
| `/update <option>` | Staff | Posts or updates the channels, notifications, welcome, or rules message. Pass a message ID to update an existing message. |
| `/station_prefix update-voice` | Staff | Updates the nicknames of everyone in a voice channel. |
| `/maintenance nick <member>` | Tech | Overrides a member's nickname. |
| `/say`, `/delete`, `/ping` | Staff | Small moderation helpers. |
| `/load`, `/unload`, `/reload`, `/cogs` | Staff | Manages the bot's cogs at runtime. |

## Project layout

| Path | Contents |
| --- | --- |
| `bot.py` | Entry point, error handling, and startup. |
| `cogs/` | One module per feature area, loaded at startup. |
| `core/` | Shared building blocks such as logging and role helpers. New shared code belongs here. |
| `helpers/` | Older shared code, including configuration and API clients. |
| `messages/` | Markdown sources for the messages the bot posts. |
| `tests/` | Test suite. |
| `docs/` | Extra documentation, such as the [logging format](docs/logging.md). |

## Develop and test

The repository uses mise tasks. Run them with `mise run <task>`, or run the underlying commands with `uv run` directly.

| Task | Command |
| --- | --- |
| Start the bot | `mise run dev` |
| Run the tests | `mise run test` |
| Check formatting, lint, and types | `mise run lint` |
| Fix formatting and lint issues | `mise run fix` |

Formatting and linting use Ruff, type checking uses mypy, and tests use pytest. CI runs the same tasks and builds the container image.

Logging goes through `core/logging.py`. It prints readable console output when `DEBUG` is on and logfmt when it is off. See [docs/logging.md](docs/logging.md) for details.

## Contribute

Contributions are much appreciated. Fork the repository so you can open pull requests back to the main project.

To keep the project consistent, follow these conventions:

- Name branches `topic/name-here`, for example `topic/new-api` or `topic/new-staffing-system`.
- Write commit messages in the [Conventional Commits](https://www.conventionalcommits.org/) style, for example `fix(roles): remove old rating roles`. Releases and the changelog are generated from them.
- Run `mise run lint` and `mise run test` before you open a pull request.

[events]: https://github.com/vatsim-scandinavia/events
[control-center]: https://github.com/vatsim-scandinavia/controlcenter
