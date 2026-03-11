# VATSIM Scandinavia Discord Bot

The VATSIM Scandinavia Discord Bot is created by [Markus N.](https://github.com/Marko259) (1401513), [Daniel L.](https://github.com/blt950) (1352906), and [Thor H.](https://github.com/thor) (1512667).

Open-sourced for contributions, please read the license before you copy any of the code.

## About

Our Discord bot does the following:

- Verify VATSIM Scandinavia members by using the CID provided and already verified by the global VATSIM bot
- Post events in events channel and create events notifications when they're about to start
- Make staffing channels in Discord together with [the event system][events]
- Update rules and other messages on request
- Other smaller services

## Prerequisites

- Python 3.13
- uv

## How to install

- Configure the bot through `.env`, no settings should be empty when done
- Install all dependencies with `uv sync` or by using the exported requirements
- Run the bot with `bot.py`, e.g. `uv run python bot.py` or `python bot.py`

## Configuration

Not all of the configuration settings in `.env` are documented. Here's a brief explanation for a few of the most important settings:

- `VATSIM_CHECK_MEMBER_URL` is the VATSIM API memberlist for your subdivision, e.g, `https://api.vatsim.net/api/subdivisions/SCA/members/?paginated`
- `VATSIM_SUBDIVISION` is the short abbriviation of your subdivision e.g. `SCA`
- `DIVISION_URL` is the full URL to your homepage e.g `https://vatsim-scandinavia.org`
- `EVENT_CALENDAR_URL` is the API URL for your Invision Forum installation if you have any
- `CC_API_URL` and TOKEN is the [Control Center][control-center] API connection if you use it.
- `*_ROLE` are your Discord Role ID's for the respective ratings.

### Role Configuration
The bot automatically assigns Discord roles based on data from the Control Center API:

- `MENTOR_ROLE` - Discord role ID for members with Mentor status
- `BUDDY_ROLE` - Discord role ID for members with Buddy status
- `TRAINING_STAFF_ROLE` - Discord role ID for Training Staff/Moderators
- `VISITOR_ROLE` - Discord role ID for Visiting Controllers

### FIR-Specific Roles
You can configure FIR-specific roles that are assigned based on which FIR a member has a particular role in:

- `FIR_DATA` - Mentor roles per FIR, format: `FIR:RoleID,FIR:RoleID` (e.g., `Denmark:1234567890,Norway:1234567891,Sweden:1234567892`)
- `BUDDY_DATA` - Buddy roles per FIR, same format as FIR_DATA (e.g., `Denmark:1234567890,Norway:1234567891,Sweden:1234567892`)
- `EXAMINER_DATA` - Examiner roles per FIR, same format as FIR_DATA

See `.env.example` for a complete list of all available configuration options.

### Reaction Role Configuration

`REACTION_ROLE_DATA` follows the format `:emoji_name:|message_id|role_id` with multiple entries separated by commas:
```
REACTION_ROLE_DATA=:calendar:|1234567890|0987654321,:airplane:|1234567890|1234509876
```

**Important: Emoji names must exactly match what the `emoji` library produces at runtime.** The name you see in Discord or online may differ from what the bot uses internally, which will cause reactions to be silently ignored.

To find the correct name for an emoji, run the following in your terminal:
```bash
python3 -m venv venv
source venv/bin/activate
pip install emoji==2.12.1
python3 -c "import emoji; print(emoji.demojize('🌍'))"
```

Replace `🌍` with your desired emoji. Use the output (e.g. `:globe_showing_Europe-Africa:`) as the emoji name in `REACTION_ROLE_DATA`.

**The message IDs must match the actual Discord messages the bot has posted.** After the bot creates the reaction role messages, right-click each message in Discord → *Copy Message ID* and update `REACTION_ROLE_DATA` accordingly, then restart the bot.

## Contribution and conventions

Contributions are much appreciated to help everyone move this service forward with fixes and functionalities. We recommend you to fork this repository here on GitHub so you can easily create pull requests back to the main project.

In order to keep a collaborative project in the same style and understandable, it's important to follow some conventions:

### GitHub Branches

We name branches with `topic/name-here` including fixes and features, for instance `topic/new-api` or `topic/new-staffing-system`

[events]: https://github.com/vatsim-scandinavia/events
[control-center]: https://github.com/vatsim-scandinavia/controlcenter
