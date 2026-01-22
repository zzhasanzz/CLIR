import scrapy
import json


class BanglaTribuneCountrySpider(scrapy.Spider):
    name = "banglatribune_country"
    allowed_domains = ["banglatribune.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 1,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO"
    }

    # Division AJAX configuration
    divisions = {
        "dhaka":      {"page_id": "717", "tags": "15"},
        "chitagong": {"page_id": "717", "tags": "12"},
        "rajshahi":   {"page_id": "717", "tags": "19"},
        "khulna":     {"page_id": "717", "tags": "17"},
        "barishal":   {"page_id": "717", "tags": "20"},
        "sylhet":     {"page_id": "717", "tags": "11"},
        "rangpur":    {"page_id": "717", "tags": ""},   # try blank
        "mymensing": {"page_id": "717", "tags": "9"},
    }

    # max articles per division
    max_per_division = 60

    def start_requests(self):
        for division, p in self.divisions.items():
            url = f"https://www.banglatribune.com/country/{division}"
            yield scrapy.Request(
                url,
                callback=self.parse_section,
                cb_kwargs={"division": division, "params": p}
            )

    def parse_section(self, response, division, params):
        initial_links = self.extract_links(response)
        yield from self.queue_links(response, initial_links, division)

        yield scrapy.Request(
            url=self.build_api_url(
                start=20,
                page_id=params["page_id"],
                tags=params["tags"]
            ),
            callback=self.parse_api,
            meta={"start": 20, "total": len(initial_links),
                  "division": division, **params},
            headers={
                "X-Requested-With": "XMLHttpRequest",
                "Referer": response.url,
                "Accept": "application/json, text/javascript, */*; q=0.01"
            }
        )

    def parse_api(self, response):
        data = json.loads(response.text)
        html = data.get("html")

        division = response.meta["division"]
        page_id = response.meta["page_id"]
        tags = response.meta["tags"]
        total = response.meta["total"]
        start = response.meta["start"]

        if not html:
            self.logger.warning("No HTML in API response for %s", division)
            return

        selector = scrapy.Selector(text=html)
        links = self.extract_links(selector)

        self.logger.info("AJAX found %d links for %s", len(links), division)
        yield from self.queue_links(response, links, division)

        total += len(links)

        if total < self.max_per_division and links:
            next_start = start + 20
            yield scrapy.Request(
                url=self.build_api_url(start=next_start, page_id=page_id, tags=tags),
                callback=self.parse_api,
                meta={
                    "division": division,
                    "page_id": page_id,
                    "tags": tags,
                    "start": next_start,
                    "total": total
                },
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"https://www.banglatribune.com/country/{division}",
                    "Accept": "application/json, text/javascript, */*; q=0.01"
                }
            )

    def extract_links(self, selector):
        return selector.css("a.link_overlay::attr(href)").getall()

    def queue_links(self, response, links, division):
        for link in links:
            yield response.follow(
                link, callback=self.parse_article,
                cb_kwargs={"division": division}
            )

    def parse_article(self, response, division):
        paragraphs = response.xpath(
            "//div[contains(@class, 'jw_article_body')]//p//text()"
        ).getall()

        body = " ".join(t.strip().replace("\xa0", " ") for t in paragraphs if t.strip())

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
            "section": division
        }

    def build_api_url(self, start, page_id, tags):
        # tags may be blank for Rangpur
        return (
            "https://www.banglatribune.com/api/theme_engine/get_ajax_contents"
            "?widget=10944"
            f"&start={start}"
            "&count=20"
            f"&page_id={page_id}"
            "&author=0"
            f"&tags={tags}"
            "&archive_time="
            "&filter="
        )
