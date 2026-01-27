# ElearnOBot

A discord bot for receiving course updates notifications and convenient file and announcement management, designed and tested for Aristotle University of Thessaloniki.

## License
This project and its source code is licensed under GNU General Public License version 3. Check [license file](./LICENSE) for more details.

## Features
- Moodle API compatible
- Receive notifications when any of the following is _created_, _modified_ or _deleted_;
    1. Files
    2. Pages
    3. Forums and Discussions
    4. Workshops
    5. Quizzes
    6. Assignments
- Fully customizable by using a convenient [configuration file](./config.cfg)
- Easily deployable by using Docker Compose

## Installation
Please follow the steps below:

1. Python 3.9 or greater is required. Please make sure Python is available on your system.
2. Create a Python virtual environment (venv): `python3 -m venv .venv`
3. Activate the virtual environment you just created: `source .venv/bin/activate`
4. Fill the example configuration file with your own settings. The following options must be specified, otherwise program will be unable to run;
    - Moodle API key
    - Moodle User ID
    - Discord bot token
    - Discord channel ID for notifications
    - The hostname of moodle instance (for example `elearning.auth.gr` for A.U.Th.)
    - Database path on which application's database is created/located
    - In case you want to save all files found by the bot, specify the download directory as well
5. Run bot: `python3 bot.py -c <path/to/config/file.cfg>`. Specifying the configuration file is optional. By default `config.py` will be used of your current working directory.

## Other notes about bot usage
> [!TIP]
> Moodle API key and user ID can also be obtained and automatically refreshed within discord, by issuing the `updatetoken` command and entering the URL provided by scanning your personal QR code!

> [!NOTE]
> Moodle API token may expire according to the configuration of each moodle instance. In the case of `elearning.auth.gr` expires every 6 months. You will receive notification when this happens. Token can again be automatically refresh by using the `updatetoken` command, as specified above.

> [!WARN]
> Use a rational update check interval and enable interval randomization, otherwise you may get suspended from the moodle instance of your university, if you set the interval too low!