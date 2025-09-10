import os

class Config(object):
     
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    API_ID = int(os.environ.get("API_ID", "25331263" ))
    API_HASH = os.environ.get("API_HASH", "cab85305bf85125a2ac053210bcd1030")
    #Add your channel id. For force Subscribe.
    CHANNEL = os.environ.get("CHANNEL", "-1002888391802")
    #Skip or add your proxy from https://github.com/rg3/youtube-dl/issues/1091#issuecomment-230163061
    HTTP_PROXY = ''
