import scrapy
import json


class BanglaTribuneLatestSpider(scrapy.Spider):
    name = "banglatribune_latest"
    allowed_domains = ["banglatribune.com"]

    start_urls = [
        "https://www.banglatribune.com/আজকের-খবর"
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO"
    }

    def parse(self, response):
        links = self.extract_links(response)
        yield from self.queue_links(response, links)

        yield scrapy.Request(
            url=self.build_api_url(start=20),
            callback=self.parse_api,
            meta={"start": 20, "total": len(links)},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": response.url,
                "Accept": "application/json, text/javascript, */*; q=0.01"
            }
        )

    def parse_api(self, response):
        data = json.loads(response.text)
        html = data.get("html")

        if not html:
            self.logger.warning("No HTML in API response")
            return

        selector = scrapy.Selector(text=html)
        links = self.extract_links(selector)

        self.logger.info("New links from API: %d", len(links))
        yield from self.queue_links(response, links)

        total = response.meta["total"] + len(links)
        start = response.meta["start"]

        if total < 100 and links:
            next_start = start + 20
            yield scrapy.Request(
                url=self.build_api_url(start=next_start),
                callback=self.parse_api,
                meta={"start": next_start, "total": total},
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": "https://www.banglatribune.com/আজকের-খবর",
                    "Accept": "application/json, text/javascript, */*; q=0.01"
                }
            )

    def extract_links(self, selector):
        return selector.css(
            "a.link_overlay::attr(href)"
        ).getall()

    def queue_links(self, response, links):
        for link in links:
            yield response.follow(link, self.parse_article)

    def parse_article(self, response):
        paragraphs = response.xpath(
            "//div[contains(@class,'jw_article_body')]//p//text()"
        ).getall()

        body = " ".join(
            t.strip().replace("\xa0", " ")
            for t in paragraphs
            if t.strip()
        )

        yield {
            "title": response.css("h1.title::text").get(),
            "body": body,
            "url": response.url,
            "date": response.css("span.tts_time::text").get(),
            "language": "bn",
            "author": response.css(
                "div.each_row.author_n_share span.name::text"
            ).get(),
            "tokens": len(body.split()),
        }


    def build_api_url(self, start):
        return (
            "https://www.banglatribune.com/api/theme_engine/get_ajax_contents"
            "?widget=10950"
            f"&start={start}"
            "&count=20"
            "&page_id=0"
            "&author=0"
            "&tags="
            "&archive_time="
            "&filter="
        )
