import requests


class BaseScraper:
    def __init__(self):
        self.session = requests.Session()
