import bs4
from scrapers.base_scraper import BaseScraper


"""

"""


class InfoMatchScraper(BaseScraper):
    def get_details(self, url: str) -> dict:
        info = {}
        res = self.session.get(url)
        res.raise_for_status()
        soup = bs4.BeautifulSoup(res.text, "html.parser")

        labels = soup.find_all("b")
        for b in labels:
            key = b.get_text(strip=True).rstrip(":")
            # get text after the <b> tag up to the next <br>
            value = b.next_sibling.strip() if b.next_sibling else None
            info[key] = value

        iframe = soup.find("iframe")
        if iframe and iframe.has_attr("src"):
            info["maps_url"] = iframe["src"].replace("&output=embed", "")

        return info
