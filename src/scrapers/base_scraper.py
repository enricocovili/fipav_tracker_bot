import requests
import bs4


class BaseScraper:
    def __init__(self):
        self.session = requests.Session()

    