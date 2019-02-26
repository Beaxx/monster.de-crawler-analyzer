import requests


class RequestManager:
    @staticmethod
    def unauthenticated_request(url):
        return requests.get(url)
