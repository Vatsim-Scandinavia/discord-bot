# VATSIM Scandinavia Discord Bot

VATSIM Scandinavia Bot is created by and [Markus N.](https://github.com/Marko259) (1401513) and  [Daniel L.](https://github.com/blt950) (1352906).

Open sourced for contributions, please read the license before you copy any of the code.

## About
Our Discord bot is created to do the following task
- Verify VATSIM Scandinavia members by using the CID provided and already verified by VATSIM bot
- Post events in events channel and tag events notification when it's about to start
- Make staffing threads in Discord directly
- Update rules and other messages on request
- Other misc things

## Prerequisites
- Python 3.7+ recommended
- MySQL Server v.8.0+
- Invision Forum Calendar API for event functionality

## How to install
- Make sure you've Python 3.7 or higher installed in your environment
- Install all dependecies by doing `pip3 install -r requirements.txt` or manually one by one
- Setup the configurations in `.env`, none of them should be zero when finished
- Run the bot with `python3 bot.py`

### Configuration
Since not all lines of the environment file, here's an explanation for a few

- `VATSIM_CHECK_MEMBER_URL` is the VATSIM API memberlist for your subdivision, e.g, `https://api.vatsim.net/api/subdivisions/SCA/members/?paginated`
- `VATSIM_SUBDIVISION` is the short abbriviation of your subdivision e.g. `SCA`
- `DIVISION_URL` is the full url to your homepage e.g `https://vatsim-scandinavia.org`
- `EVENT_CALENDAR_URL` is the API URL for your Invision Forum installation if you have any
- `CC_API_URL` and TOKEN is the [Control Center](https://github.com/Vatsim-Scandinavia/controlcenter) API connection if you use it.
- `*_ROLE` are your Discord Role ID's for the respective ratings.

## Contribution and conventions
Contributions are much appreciated to help everyone move this service forward with fixes and functionalities. We recommend you to fork this repository here on GitHub so you can easily create pull requests back to the main project.

In order to keep a collaborative project in the same style and understandable, it's important to follow some conventions:

##### GitHub Branches
We name branches with `topic/name-here` including fixes and features, for instance `topic/new-api` or `topic/new-staffing-system`
