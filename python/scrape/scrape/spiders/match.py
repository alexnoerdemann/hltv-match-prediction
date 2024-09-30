import re
from datetime import datetime as dt
from enum import Enum

import scrapy


# TODO[HMP-TASK-4]: Add docstring(s) for everything
class MatchSpider(scrapy.Spider):
    class MapResult:
        class RoundHistorySource(Enum):
            UNKNOWN = 0
            SCOREBOARD = 1
            STATS_PAGE = 2

        class TeamMapResult:
            def __init__(self) -> None:
                self.teamname: str | None = None
                self.score: int | None = None
                self.firsthalf: list | None = None
                self.secondhalf: list | None = None
                # TODO[HMP-TASK-4]: Refine how to set and get the overtime, since we expect it to be a list of lists.
                self.overtime: list | None = None

        def __init__(self) -> None:
            self.source = self.RoundHistorySource.UNKNOWN
            self.mapname: str | None = None
            self.toppart_team_result = self.TeamMapResult()
            self.bottompart_team_result = self.TeamMapResult()

    BASE_SCRAPE_ERROR_STRING = "scrape-error"
    name = "match"

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        if "start_urls" in kwargs:
            spider.start_urls = kwargs.pop("start_urls").split(",")
        spider.allowed_domains = crawler.settings.get("SPIDER_ALLOWED_DOMAINS", [])

        return spider

    def __parse_match_id(self, response) -> int:
        return int(re.search(r"\d+", response.url).group())

    def __parse_event(self, response) -> dict[str, str | None]:
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

    def __parse_teams(self, response) -> dict[str, list[str]]:
        lineup = response.css("div.lineup")
        output = dict()
        for index, team in enumerate(lineup):
            teamname = team.css(
                "div.box-headline.flex-align-center a.text-ellipsis::text"
            ).get(default=self.BASE_SCRAPE_ERROR_STRING + f"-team-{index+1}-not-found")
            players = team.css(
                "div.players table.table td.player div.text-ellipsis::text"
            ).getall()
            output.update({teamname: players})

        return output

    def __parse_best_of(self, response) -> int | None:
        best_of = response.css(".preformatted-text::text").get()
        return int(re.search(r"\d+", best_of).group()) if best_of else None

    def __parse_map_result_from_stats_link(self, link) -> dict[str, MapResult]:
        # TODO[HMP-TASK-4]: Crawl and parse data from "stats page"
        return {"map_result": self.MapResult()}

    def __parse_map_result_from_scoreboard(self, response) -> dict[str, MapResult]:
        # HLTV Scoreboard works as follows:
        # - First Half: The team which starts as CT is at the top part of the board, the other at the bottom.
        # - Second Half: The team at the top switches to the bottom and vice versa. The round history flips.
        # - Overtime:
        #       -- No top-bottom-switches appear, i.e. stays the same as in the "Second Half".
        #       -- No more updates in the ".roundHistory" CSS Selector. Current score needs to be selected from, e.g. the ".score" Selector.
        def parse_mapname(response) -> str | None:
            output = response.css(".currentRoundText *::text").getall()
            if output:
                output = "".join(output).strip()
                output = output.rsplit(None, 1)[-1]
                output = output.capitalize()
            else:
                output = None
            return output
        def parse_teamname(response, selector: str) -> str | None:
            output = response.css(selector).getall()
            if output:
                output = "".join(output).strip()
            else:
                output = None
            return output

        def parse_half(response, halfselector: str) -> tuple[list[bool]]:
            def transform_half_to_round_list(half):
                return [
                    False if "empty" in round else True
                    for round in half.css("div.historyIcon img::attr(src)").getall()
                ]

            toppart_half = []
            bottompart_half = []
            halfs = response.css(halfselector)
            for index, half in enumerate(halfs):
                if index == 0:
                    toppart_half = transform_half_to_round_list(half)
                else:
                    bottompart_half = transform_half_to_round_list(half)

            return (toppart_half, bottompart_half)

        result = self.MapResult()
        result.source = self.MapResult.RoundHistorySource.SCOREBOARD
        result.mapname = parse_mapname(response)
        result.toppart_team_result.teamname = parse_teamname(
            response,
            ".ctTeamHeaderBg > tr:nth-child(1) > td:nth-child(1) > div:nth-child(1) *::text",
        )
        result.toppart_team_result.score = response.css(".ctScore::text").get()
        result.bottompart_team_result.teamname = parse_teamname(
            response,
            ".tTeamHeaderBg > tr:nth-child(1) > td:nth-child(1) > div:nth-child(1) *::text",
        )
        result.bottompart_team_result.score = response.css(".tScore::text").get()
        (
            result.toppart_team_result.firsthalf,
            result.bottompart_team_result.firsthalf,
        ) = parse_half(response, ".firstHalf div.roundHistoryLine")
        (
            result.toppart_team_result.secondhalf,
            result.bottompart_team_result.secondhalf,
        ) = parse_half(response, ".secondHalf div.roundHistoryLine")

        return {"map_result": result}

    def parse(self, response):
        yield {"match_id": self.__parse_match_id(response)}
        yield {"event": self.__parse_event(response)}
        yield {"teams": self.__parse_teams(response)}
        yield {"best-of": self.__parse_best_of(response)}

        # Inspecting different HLTV match behaviors, we assume the following:
        # - Every finished map has a "STATS" element and we crawl and parse the per round data from there.
        # - There is only one ongoing map and its per round data can be retrieved from the "Scoreboard".
        for map in response.css("div.mapholder"):
            stats_link = map.css(".results-stats::attr(href)").get()
            if stats_link is not None:
                yield scrapy.Request(
                    url=stats_link,
                    callback=self.__parse_map_result_from_stats_link,
                )
            else:
                yield self.__parse_map_result_from_scoreboard(response)
                break
