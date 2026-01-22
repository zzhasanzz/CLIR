import scrapy


class DailyNewNationNationalSpider(scrapy.Spider):
    name = "dailynewnation_sports"
    allowed_domains = ["dailynewnation.com"]

    BASE_URL = "https://dailynewnation.com/news/category/todays-news/sports/"
    MAX_PAGES = 50
    MAX_ARTICLES = 200

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
        "FEED_EXPORT_ENCODING": "utf-8",
        "LOG_LEVEL": "INFO",
    }

    page_no = 1
    item_count = 0
    seen_urls = set()

    # --------------------------------------------------
    # START
    # --------------------------------------------------
    def start_requests(self):
        yield scrapy.Request(
            url=self.BASE_URL,
            callback=self.parse,
            meta={"page": 1}
        )

    # --------------------------------------------------
    # LISTING PAGE
    # --------------------------------------------------
    def parse(self, response):
        page = response.meta["page"]

        links = response.css(
            "h2.post-title.entry-title a::attr(href)"
        ).getall()

        self.logger.info(
            "Page %d → %d article links",
            page,
            len(links)
        )

        if not links:
            self.logger.info("No links found → stopping pagination")
            return

        for link in links:
            if self.item_count >= self.MAX_ARTICLES:
                return

            if link in self.seen_urls:
                continue

            self.seen_urls.add(link)
            yield response.follow(link, self.parse_article)

        # 🔥 MANUAL PAGINATION
        if page < self.MAX_PAGES and self.item_count < self.MAX_ARTICLES:
            next_page = page + 1
            next_url = f"{self.BASE_URL}/page/{next_page}/"

            yield scrapy.Request(
                url=next_url,
                callback=self.parse,
                meta={"page": next_page}
            )

    # --------------------------------------------------
    # ARTICLE PAGE
    # --------------------------------------------------
    def parse_article(self, response):
        if self.item_count >= self.MAX_ARTICLES:
            return

        title = response.css(
            "h1.post-title.entry-title::text"
        ).get()

        date = response.css(
            "time.published::text"
        ).get()

        paragraphs = response.css(
            "div.entry-inner p::text"
        ).getall()

        body = " ".join(p.strip() for p in paragraphs if p.strip())

        # filter junk / very short items
        if len(body.split()) < 30:
            return

        self.item_count += 1

        yield {
            "title": title.strip() if title else None,
            "body": body,
            "url": response.url,
            "date": date.strip() if date else None,
            "language": "en",
            "author": "Daily New Nation",
            "section": "sports",
            "tokens": len(body.split())
        }
