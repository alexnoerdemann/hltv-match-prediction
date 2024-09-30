import copy
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
                self.firsthalf: list[bool] | None = None
                self.secondhalf: list[bool] | None = None
                self.overtime: list[list[bool]] | None = None

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

    def __parse_map_result_from_stats_link(
        self, stats_response
    ) -> dict[str, MapResult]:
        def parse_round_history_team_row(
            stats_response, selector: str
        ) -> list[list[bool]]:
            """Parses the whole round history of the team including potential overtimes."""
            output = list()
            history = stats_response.css(selector).xpath("child::*")
            history_part = list()
            for item in history:
                node = item.get()
                node_type = item.xpath("name()").get()
                if node_type == "img" and "round-history-team" not in node:
                    # TODO[HMP-TASK-?]: We might need smarter filtering for the actual win/loss condition.
                    history_part.append(False if "empty" in node else True)
                elif node_type == "div":
                    output.append(copy.deepcopy(history_part))
                    history_part.clear()
            else:
                # Also append the parsed rounds to the output, which came after the last separating "div/vertical bar".
                if history_part:
                    output.append(copy.deepcopy(history_part))

            # We have to remove list(s) from the output to get rid of wrongly parsed data (e.g. the very start with the team logos and the div/vertical bar).
            return list(filter(lambda elem: len(elem) > 2, output))

        result = self.MapResult()
        result.source = self.MapResult.RoundHistorySource.STATS_PAGE
        match_info_box = stats_response.css(".match-info-box *::text").getall()
        if match_info_box:
            try:
                result.mapname = match_info_box[4].strip()
                result.toppart_team_result.teamname = match_info_box[5]
                result.toppart_team_result.score = int(match_info_box[7])
                result.bottompart_team_result.teamname = match_info_box[10]
                result.bottompart_team_result.score = int(match_info_box[12])
            except IndexError:
                # No special handling needed here, since all values are defaulted to None.
                pass

        try:
            toppart_round_history = parse_round_history_team_row(
                stats_response, "div.round-history-team-row:nth-child(1)"
            )
            result.toppart_team_result.firsthalf = toppart_round_history[0]
            result.toppart_team_result.secondhalf = toppart_round_history[1]
            result.toppart_team_result.overtime = toppart_round_history[2:]
        except IndexError:
            # No special handling needed here, since all values are defaulted to None.
            pass

        try:
            bottompart_round_history = parse_round_history_team_row(
                stats_response, "div.round-history-team-row:nth-child(2)"
            )
            result.bottompart_team_result.firsthalf = bottompart_round_history[0]
            result.bottompart_team_result.secondhalf = bottompart_round_history[1]
            result.bottompart_team_result.overtime = bottompart_round_history[2:]
        except IndexError:
            # No special handling needed here, since all values are defaulted to None.
            pass

        return {"map_result": result}

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
                # TODO[HMP-TASK-?]: We might need smarter filtering for the actual win/loss condition.
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
