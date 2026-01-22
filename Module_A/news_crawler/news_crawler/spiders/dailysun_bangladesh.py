import scrapy
import cloudscraper
from scrapy.selector import Selector


class DailySunBangladeshSpider(scrapy.Spider):
    name = "dailysun_bangladesh"

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
    }

    MAX_ARTICLES = 200

    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True,
        }
    )

    seen_urls = set()
    item_count = 0
    last_id = 0

    # --------------------------------------------------
    # ENTRY
    # --------------------------------------------------
    def start_requests(self):
        self.logger.info("Fetching listing HTML via cloudscraper")

        html = self.scraper.get(
            "https://www.daily-sun.com/bangladesh",
            timeout=20
        ).text

        selector = Selector(text=html)

        links = selector.css("a.linkOverlay::attr(href)").getall()
        self.logger.info("HTML → %d links", len(links))

        for link in links:
            if self.item_count >= self.MAX_ARTICLES:
                return

            self.seen_urls.add(link)
            yield from self.fetch_article(link)

        yield from self.fetch_ajax()

    # --------------------------------------------------
    # AJAX LOOP
    # --------------------------------------------------
    def fetch_ajax(self):
        while self.item_count < self.MAX_ARTICLES:
            url = (
                "https://www.daily-sun.com/ajax/load/categorynews/"
                f"1/20/2/20?lastID={self.last_id}"
            )

            self.logger.info("AJAX → lastID=%s", self.last_id)

            r = self.scraper.get(url, timeout=20)

            if r.status_code != 200:
                self.logger.info("AJAX blocked → stopping")
                return

            data = r.json()
            if not data:
                self.logger.info("No more AJAX data")
                return

            new = 0

            for item in data:
                article_url = item.get("url")
                article_id = item.get("id")

                if not article_url or article_url in self.seen_urls:
                    continue

                self.seen_urls.add(article_url)
                self.last_id = article_id
                new += 1

                yield from self.fetch_article(article_url)

            if new == 0:
                self.logger.info("No new links → stopping AJAX")
                return

    # --------------------------------------------------
    # ARTICLE FETCH (cloudscraper, NOT Scrapy)
    # --------------------------------------------------
    def fetch_article(self, url):
        if self.item_count >= self.MAX_ARTICLES:
            return

        r = self.scraper.get(url, timeout=20)

        if r.status_code != 200:
            return

        selector = Selector(text=r.text)

        title = selector.css("h1.detailHeadline::text").get()
        author = selector.css("p.detailReporter strong::text").get()
        date = selector.css("span.publishedTime::text").get()

        paragraphs = selector.css(
            "div.detailContent p::text, p.MsoNormal::text"
        ).getall()

        body = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(body.split()) < 40:
            return

        self.item_count += 1

        yield {
            "title": title.strip() if title else None,
            "body": body,
            "url": url,
            "date": date.replace("Published:", "").strip() if date else None,
            "language": "en",
            "author": author.strip() if author else "Daily Sun",
            "section": "bangladesh",
            "tokens": len(body.split())
        }
