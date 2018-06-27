import json
import requests
import urllib
from tokenbot import catch_token


class Url:

    token = ""
    url = ""

    def __init__(self):
        self.token = catch_token()
        self.url = "https://api.telegram.org/bot{}/".format(self.token)

    @staticmethod
    def get_url(url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = self.url + "getUpdates?timeout=100"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def send_message(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        msg_mark = "sendMessage?text={}&chat_id={}&parse_mode=Markdown"
        url = self.url + msg_mark.format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)
