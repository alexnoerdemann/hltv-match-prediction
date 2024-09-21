from datetime import datetime as dt
import re

import scrapy


class MatchSpider(scrapy.Spider):
    # TODO[HMP-TASK-4]: Add docstring(s)
    name = "match"
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        if "start_urls" in kwargs:
            spider.start_urls = kwargs.pop('start_urls').split(',')
        spider.allowed_domains = crawler.settings.get('SPIDER_ALLOWED_DOMAINS', [])

        return spider

    def __parse_match_id(self, response):
        return re.search(r"\d+", response.url).group()

    def __parse_event(self, response) -> dict:
        output = {"name": None, "datetime": None}
        event_data = response.css(".teamsBox")
        date = event_data.css("div.date::text").get()
        time = event_data.css("div.time::text").get()
        name = event_data.css("div.event ::text").get()
        if None not in {date, time, name}:
            # Remove all whitespaces from the date.
            date = re.sub(r"\s+", "", date)
            # Replace all ordinal day numbers by normal day numbers.
            date = re.sub(r"(\d)(st|nd|rd|th)", r"\1", date)
            # Format and combine data to one datetime.
            formatted_date = dt.strptime(date, "%dof%B%Y")
            formatted_time = dt.strptime(time, "%H:%M")
            formatted_datetime = dt.combine(
                formatted_date.date(), formatted_time.time()
            )
            output["name"] = name
            output["datetime"] = formatted_datetime.isoformat()

        return output

    def __parse_teams(self, response):
        lineup = response.css("div.lineup")
        output = dict()
        for index, team in enumerate(lineup):
            teamname = team.css(
                "div.box-headline.flex-align-center a.text-ellipsis::text"
            ).get(default=f"scrape-error-team-{index+1}-not-found")
            players = team.css(
                "div.players table.table td.player div.text-ellipsis::text"
            ).getall()
            output.update({teamname: players})

        return output

    def parse(self, response):
        yield {
            "match_id": self.__parse_match_id(response),
            "event": self.__parse_event(response),
            "teams": self.__parse_teams(response),
        }
