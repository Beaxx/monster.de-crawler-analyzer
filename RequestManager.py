import definitions
import requests


class RequestManager:
    def __init__(self):
        pass

    def unauthenticated_request(self, url):
        return requests.get(url)
