import scrapy
import json
from scrapy.selector import Selector


class DailyStarAgricultureSpider(scrapy.Spider):
    name = "thedailystar_agriculture"
    allowed_domains = ["thedailystar.net"]

    start_urls = [
        "https://www.thedailystar.net/news/bangladesh/agriculture"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
        "FEED_EXPORT_ENCODING": "utf-8",
        "LOG_LEVEL": "INFO",
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    }

    MAX_ARTICLES = 200

    # runtime state
    seen_urls = set()
    item_count = 0

    # --------------------------------------------------
    # INITIAL PAGE
    # --------------------------------------------------
    def parse(self, response):
        links = self.extract_links(response)
        self.logger.info("Initial page → %d article links", len(links))

        yield from self.queue_articles(response, links)

        # AJAX pagination starts from page=1
        yield scrapy.Request(
            url=self.build_ajax_url(page=1),
            callback=self.parse_ajax,
            meta={"page": 1},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Referer": response.url
            }
        )

    # --------------------------------------------------
    # AJAX PAGINATION
    # --------------------------------------------------
    def parse_ajax(self, response):
        page = response.meta["page"]

        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.info("AJAX page %s → invalid JSON, stopping", page)
            return

        # 🔥 Correct Drupal command
        html_parts = [
            item.get("data", "")
            for item in data
            if item.get("command") == "viewsShowMore"
        ]

        html = "\n".join(html_parts)

        if not html.strip():
            self.logger.info("AJAX page %s → empty HTML, stopping", page)
            return

        selector = Selector(text=html)

        links = self.extract_links(selector)
        self.logger.info("AJAX page %s → %d links", page, len(links))

        yield from self.queue_articles(response, links)

        if self.item_count >= self.MAX_ARTICLES:
            self.logger.info("Reached MAX_ARTICLES (%d)", self.MAX_ARTICLES)
            return

        yield scrapy.Request(
            url=self.build_ajax_url(page + 1),
            callback=self.parse_ajax,
            meta={"page": page + 1},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
                "Referer": "https://www.thedailystar.net/news/bangladesh/agriculture"
            }
        )

    # --------------------------------------------------
    # LINK EXTRACTION
    # --------------------------------------------------
    def extract_links(self, selector):
        return selector.css(
            "a[href^='/news/']::attr(href)"
        ).getall()

    # --------------------------------------------------
    # QUEUE ARTICLES
    # --------------------------------------------------
    def queue_articles(self, response, links):
        for link in links:
            if self.item_count >= self.MAX_ARTICLES:
                return

            abs_url = response.urljoin(link)

            if abs_url in self.seen_urls:
                continue

            self.seen_urls.add(abs_url)
            yield response.follow(abs_url, self.parse_article)

    # --------------------------------------------------
    # ARTICLE PARSER
    # --------------------------------------------------
    def parse_article(self, response):
        if self.item_count >= self.MAX_ARTICLES:
            return

        paragraphs = response.css(
            "div.block-field-blocknodenewsbody p::text"
        ).getall()

        body = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(body.split()) < 30:
            return

        title = response.css(
            "div.block-field-blocknodenewstitle h1::text"
        ).get()

        author = response.css(
            ".block-author-info-block span.font-medium::text"
        ).get()

        date = response.css(
            "span.text-gray-600::text"
        ).get()

        self.item_count += 1

        yield {
            "title": title.strip() if title else None,
            "body": body,
            "url": response.url,
            "date": date.strip() if date else None,
            "language": "en",
            "author": author.strip() if author else "The Daily Star",
            "section": "agriculture",
            "tokens": len(body.split())
        }

    # --------------------------------------------------
    # AJAX URL BUILDER (AGRICULTURE)
    # --------------------------------------------------
    def build_ajax_url(self, page):
        return (
            "https://www.thedailystar.net/views/ajax"
            "?_wrapper_format=drupal_ajax"
            "&view_name=category_show_more"
            "&view_display_id=block_1"
            "&view_args=283529"
            "&view_path=%2Ftaxonomy%2Fterm%2F283529"
            "&pager_element=0"
            f"&page={page}"
            "&_drupal_ajax=1"
        )
