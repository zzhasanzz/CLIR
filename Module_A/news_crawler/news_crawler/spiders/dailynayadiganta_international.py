import scrapy


class DailyNayaDigantaInternationalSpider(scrapy.Spider):
    name = "dailynayadiganta_international"
    allowed_domains = ["dailynayadiganta.com"]

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.5,
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    start_urls = [
        "https://dailynayadiganta.com/international"
    ]

    MAX_PAGES = 500     # safety cap
    MIN_BODY_WORDS = 30

    page_no = 1
    seen_urls = set()

    # --------------------------------------------------
    # LISTING PAGE
    # --------------------------------------------------
    def parse(self, response):
        links = response.css(
            "h3.post-card-title a::attr(href)"
        ).getall()

        new_links = 0

        for link in links:
            url = response.urljoin(link)

            if url in self.seen_urls:
                continue

            self.seen_urls.add(url)
            new_links += 1

            yield scrapy.Request(
                url=url,
                callback=self.parse_article
            )

        self.logger.info(
            "Page %s → %d links (%d new)",
            self.page_no, len(links), new_links
        )

        # STOP CONDITION
        if new_links == 0 or self.page_no >= self.MAX_PAGES:
            self.logger.info("No new links → stopping pagination")
            return

        # NEXT PAGE
        self.page_no += 1
        next_page = f"https://dailynayadiganta.com/international?page={self.page_no}"

        yield scrapy.Request(
            url=next_page,
            callback=self.parse
        )

    # --------------------------------------------------
    # ARTICLE PAGE
    # --------------------------------------------------
    def parse_article(self, response):
        title = response.css(
            "h1.post-title::text"
        ).get()

        author = response.css(
            "span.font-medium::text"
        ).get()

        date = response.css(
            "time::text"
        ).get()

        paragraphs = response.css(
            "div.richtext p::text"
        ).getall()

        body = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(body.split()) < self.MIN_BODY_WORDS:
            return

        yield {
            "title": title.strip() if title else None,
            "author": author.strip() if author else "নয়া দিগন্ত অনলাইন",
            "date": date.strip() if date else None,
            "body": body,
            "url": response.url,
            "language": "bn",
            "section": "antorjatik",
            "tokens": len(body.split()),
        }
