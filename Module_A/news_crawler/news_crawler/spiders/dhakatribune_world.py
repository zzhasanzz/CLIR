import scrapy
import json
from scrapy.selector import Selector


class DhakaTribuneWorldSpider(scrapy.Spider):
    name = "dhakatribune_world"
    allowed_domains = ["dhakatribune.com"]

    start_urls = [
        "https://www.dhakatribune.com/world"
    ]

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,              # faster
        "FEED_EXPORT_ENCODING": "utf-8",
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
    }

    MAX_ARTICLES = 200
    PAGE_SIZE = 16

    seen_urls = set()
    item_count = 0

    # --------------------------------------------------
    # INITIAL HTML PAGE
    # --------------------------------------------------
    def parse(self, response):
        links = response.css("a.link_overlay::attr(href)").getall()
        self.logger.info("HTML → %d links", len(links))

        self.queue_articles(response, links)

        # Start AJAX pagination from offset = PAGE_SIZE
        yield scrapy.Request(
            url=self.build_api_url(self.PAGE_SIZE),
            callback=self.parse_api,
            meta={"offset": self.PAGE_SIZE},
            headers={"Accept": "application/json"}
        )

    # --------------------------------------------------
    # API PAGINATION (+MORE)
    # --------------------------------------------------
    def parse_api(self, response):
        offset = response.meta["offset"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.info("Invalid JSON → stopping")
            return

        html = data.get("html")
        if not html:
            self.logger.info("No HTML → stopping")
            return

        selector = Selector(text=html)
        links = selector.css("a.link_overlay::attr(href)").getall()

        self.logger.info("API offset=%d → %d links", offset, len(links))

        new_count = 0

        for link in links:
            if self.item_count >= self.MAX_ARTICLES:
                return

            url = response.urljoin(link)

            if url in self.seen_urls:
                continue

            self.seen_urls.add(url)
            new_count += 1

            yield scrapy.Request(
                url=url,
                callback=self.parse_article,
                headers={"Referer": "https://www.dhakatribune.com/"}
            )

        # 🔥 THIS IS THE REAL STOP CONDITION
        if new_count == 0:
            self.logger.info("No NEW links → stopping pagination")
            return

        # 🔥 HARD SAFETY STOP (very important)
        if offset >= 1000:
            self.logger.info("Offset limit reached → stopping pagination")
            return

        yield scrapy.Request(
            url=self.build_api_url(offset + self.PAGE_SIZE),
            callback=self.parse_api,
            meta={"offset": offset + self.PAGE_SIZE},
            headers={"Accept": "application/json"}
        )


    # --------------------------------------------------
    # QUEUE ARTICLES (DEDUP + STOP LOGIC)
    # --------------------------------------------------
    def queue_articles(self, response, links):
        new_found = False

        for link in links:
            if self.item_count >= self.MAX_ARTICLES:
                break

            url = response.urljoin(link)

            if url in self.seen_urls:
                continue

            self.seen_urls.add(url)
            new_found = True

            yield scrapy.Request(
                url=url,
                callback=self.parse_article,
                headers={"Referer": "https://www.dhakatribune.com/"}
            )

        return new_found

    # --------------------------------------------------
    # ARTICLE PAGE
    # --------------------------------------------------
    def parse_article(self, response):
        if self.item_count >= self.MAX_ARTICLES:
            return

        title = response.css(
            "h1.title::text, h1[itemprop='headline']::text"
        ).get()

        author = response.css(
            "div.author span[itemprop='name'] span::text, "
            "span[itemprop='author'] span::text"
        ).get()

        date = response.css(
            "span.published_time::attr(content), "
            "span[itemprop='datePublished']::attr(content)"
        ).get()

        paragraphs = response.css(
            "div.content p::text, "
            "article p::text, "
            "div.story-body p::text"
        ).getall()

        body = " ".join(p.strip() for p in paragraphs if p.strip())

        # 🔥 Allow short legitimate news
        if len(body.split()) < 15:
            return

        self.item_count += 1

        yield {
            "title": title.strip() if title else None,
            "body": body,
            "url": response.url,
            "date": date,
            "language": "en",
            "author": author.strip() if author else "Dhaka Tribune",
            "section": "world",
            "tokens": len(body.split()),
        }

    # --------------------------------------------------
    # API URL BUILDER
    # --------------------------------------------------
    def build_api_url(self, offset):
        return (
            "https://www.dhakatribune.com/api/theme_engine/get_ajax_contents"
            "?widget=704"
            f"&start={offset}"
            "&count=16"
            "&page_id=1129"
            "&subpage_id=0"
            "&author=0"
            "&tags="
            "&archive_time="
            "&filter="
        )
