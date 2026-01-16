import configparser
import logging
from utils import loggingUtils
from utils import enums

def _parse_hex(setting: str) -> int:
        return int(setting, 16) 

class Config():
    def __init__(self, config_file: str):
        self._config_file = config_file
        self._parser = configparser.ConfigParser()
        # preserve case of configuration, don't convert to lowercase
        self._parser.optionxform = str
        self._loaded = False
        self._logger = logging.getLogger("ElearnOBot.Config")
        self._logger = loggingUtils.prepare_logger(self._logger)
   
   
    def load(self):
        self._parser.read(self._config_file)
        bot_settings = self._parser["bot"]
        moodle_settings = self._parser["moodle"]
        embeds_settings = self._parser["embeds"]
        embeds_colors_settings = self._parser["embeds.colors"]
        self.API_TOKEN = moodle_settings.get("API_TOKEN", "")
        self.DOMAIN = moodle_settings.get("DOMAIN", "")
        self.USERID = moodle_settings.get("USER_ID", "")
        self.SQLITE_DB_PATH = bot_settings.get("SQLITE_DB_PATH", "")
        self.BOT_TOKEN = bot_settings.get("BOT_TOKEN", "")
        self.DOWNLOAD_FILES = bot_settings.getboolean("DOWNLOAD_FILES", False)
        self.DOWNLOAD_DIR = bot_settings.get("DOWNLOAD_DIR", "")
        self.NOTIFICATION_CHANNEL = bot_settings.getint("NOTIFICATION_CHANNEL", 0)
        self.UPDATE_MINUTES = bot_settings.getint("UPDATE_MINUTES", 90)
        self.RANDOMIZE_UPDATE_INTERVAL = bot_settings.getboolean("RANDOMIZE_UPDATE_INTERVAL", True)
        self.FILES_PER_PAGE = embeds_settings.getint("FILES_PER_PAGE", 10)
        self.DISCUSSIONS_PER_PAGE = embeds_settings.getint("DISCUSSIONS_PER_PAGE", 10)
        self.FILES_PER_EMBED = embeds_settings.getint("FILES_PER_EMBED", 5)
        self.LINKS_PER_EMBED = embeds_settings.getint("LINKS_PER_EMBED", 5)
        self.DISCUSSIONS_PER_EMBED = embeds_settings.getint("DISCUSSIONS_PER_EMBED", 5)
        self.ATTACHMENTS_PER_EMBED = embeds_settings.getint("ATTACHMENTS_PER_EMBED", 5)
        self.DISCUSSION_LINES_PER_EMBED = embeds_settings.getint("DISCUSSION_LINES_PER_EMBED", 10)
        self.FILE_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("FILE_EMBED_COLOR", "0xfcca00"))
        self.LINK_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("LINK_EMBED_COLOR", "0x16f2ac"))
        self.ASSIGNMENT_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("ASSIGNMENT_EMBED_COLOR", "0x5f0e80"))
        self.DISCUSSION_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("DISCUSSION_EMBED_COLOR", "0x2afc00"))
        self.ATTACHMENT_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("ATTACHMENT_EMBED_COLOR", "0xfcca66"))
        self.FORUM_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("FORUM_EMBED_COLOR", "0xfcfcfc"))
        self.QUIZ_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("QUIZ_EMBED_COLOR", "0x00cefc"))
        self.PAGE_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("PAGE_EMBED_COLOR", "0x00a000"))
        self.WORKSHOP_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("WORKSHOP_EMBED_COLOR", "0xf4fc00"))
        self.INVALID_TOKEN_EMBED_COLOR = _parse_hex(embeds_colors_settings.get("INVALID_TOKEN_EMBED_COLOR", "0xff0000"))
        self._loaded = True
    

    def save(self):
        if self._loaded:
            bot_settings = self._parser["bot"]
            moodle_settings = self._parser["moodle"]
            embeds_settings = self._parser["embeds"]
            embeds_colors_settings = self._parser["embeds.colors"]
            # bot settings
            bot_settings["BOT_TOKEN"] = self.BOT_TOKEN
            bot_settings["SQLITE_DB_PATH"] = self.SQLITE_DB_PATH
            bot_settings["DOWNLOAD_FILES"] = str(self.DOWNLOAD_FILES)
            bot_settings["DOWNLOAD_DIR"] = self.DOWNLOAD_DIR
            bot_settings["NOTIFICATION_CHANNEL"] = str(self.NOTIFICATION_CHANNEL)
            bot_settings["UPDATE_MINUTES"] = str(self.UPDATE_MINUTES)
            bot_settings["RANDOMIZE_UPDATE_INTERVAL"] = str(self.RANDOMIZE_UPDATE_INTERVAL)
            # moodle settings
            moodle_settings["API_TOKEN"] = self.API_TOKEN
            moodle_settings["DOMAIN"] = self.DOMAIN
            moodle_settings["USER_ID"] = self.USERID
            # embed settings
            embeds_settings["FILES_PER_PAGE"] = str(self.FILES_PER_PAGE)
            embeds_settings["DISCUSSIONS_PER_PAGE"] = str(self.DISCUSSIONS_PER_PAGE)
            embeds_settings["FILES_PER_EMBED"] = str(self.FILES_PER_EMBED)
            embeds_settings["LINKS_PER_EMBED"] = str(self.LINKS_PER_EMBED)
            embeds_settings["DISCUSSIONS_PER_EMBED"] = str(self.DISCUSSIONS_PER_EMBED)
            embeds_settings["ATTACHMENTS_PER_EMBED"] = str(self.ATTACHMENTS_PER_EMBED)
            embeds_settings["DISCUSSION_LINES_PER_EMBED"] = str(self.DISCUSSION_LINES_PER_EMBED)
            # embed color settings
            embeds_colors_settings["FILE_EMBED_COLOR"] = hex(self.FILE_EMBED_COLOR)
            embeds_colors_settings["LINK_EMBED_COLOR"] = hex(self.LINK_EMBED_COLOR)
            embeds_colors_settings["ASSIGNMENT_EMBED_COLOR"] = hex(self.ASSIGNMENT_EMBED_COLOR)
            embeds_colors_settings["ATTACHMENT_EMBED_COLOR"] = hex(self.ATTACHMENT_EMBED_COLOR)
            embeds_colors_settings["FORUM_EMBED_COLOR"] = hex(self.FORUM_EMBED_COLOR)
            embeds_colors_settings["QUIZ_EMBED_COLOR"] = hex(self.QUIZ_EMBED_COLOR)
            embeds_colors_settings["PAGE_EMBED_COLOR"] = hex(self.PAGE_EMBED_COLOR)
            embeds_colors_settings["WORKSHOP_EMBED_COLOR"] = hex(self.WORKSHOP_EMBED_COLOR)
            embeds_colors_settings["INVALID_TOKEN_EMBED_COLOR"] = hex(self.INVALID_TOKEN_EMBED_COLOR)
            with open(self._config_file, "w") as f:
                self._parser.write(f)
        else:
            self._logger.warning("Trying to save an unloaded config, ignoring!", extra={"service_name": enums.ServiceName.CONFIG})