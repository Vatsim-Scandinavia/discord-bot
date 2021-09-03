# VATSIM Scandinavia Discord Bot

VATSIM Scandinavia Bot is created by Created by and [Markus N.](https://github.com/Marko259) (1401513) and  [Daniel L.](https://github.com/blt950) (1352906).

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

## How to install
- Make sure you've Python 3.7 or higher installed in your environment
- Install all dependecies by doing `pip3 install -r requirements.txt` or manually one by one
- Setup the configurations in `.env`, none of them should be zero when finished
- Run the bot with `python3 bot.py`

## Contribution and conventions
Contributions are much appreciated to help everyone move this service forward with fixes and functionalities. We recommend you to fork this repository here on GitHub so you can easily create pull requests back to the main project.

In order to keep a collaborative project in the same style and understandable, it's important to follow some conventions:

##### GitHub Branches
We name branches with `topic/name-here` including fixes and features, for instance `topic/new-api` or `topic/new-staffing-system`