import discord
from cassiopeia import riotapi
from cassiopeia.type.api.exception import APIError
from discord.ext import commands

import config
import database


class Summoner:
    """Commands relating to individual summoners."""
    riotapi.set_api_key(config.API)

    def __init__(self, bot):
        self.bot = bot
        self.database = database.Database('guilds.db')

    async def raise_exception(self, ctx, exception: str):
        """HTTP error handling"""
        if exception.error_code == 400:
            await ctx.send("400: Bad Request! Please join the support server with b!support.")
        elif exception.error_code == 403:
            await ctx.send("403: Forbidden! Most likely my API key has expired.")
        elif exception.error_code == 404:
            await ctx.send("404: Not Found! Please check the spelling of your summoner name.")
        elif exception.error_code == 415:
            await ctx.send("415: Unsupported Media Type! No clue how you triggered this one.")
        elif exception.error_code == 429:
            await ctx.send("429: Rate Limited Exceeded! Please wait a while.")
        elif exception.error_code == 500:
            await ctx.send("500: Internal Server Error! Please try again later.")
        elif exception.error_code == 503:
            await ctx.send("503: Service Unavailable! Please try again later")

    @commands.command(ignore_extra=False)
    async def stats(self, ctx, sum_name: str, region=None):
        if region is None:
            try:
                region = self.database.find_entry(ctx.guild.id)
            except TypeError:
                error_msg = ("Please specify a region, or set a default region with `b!region "
                             "set [region]`.")
                await ctx.send(error_msg)
                return

        if "'" in sum_name:
            await ctx.send("Please use quotation marks to enclose names")
            return

        await ctx.trigger_typing()
        riotapi.set_region(region)

        try:
            summoner = riotapi.get_summoner_by_name(sum_name)
            leagues = riotapi.get_league_entries_by_summoner(summoner)
            top_champ = riotapi.get_top_champion_masteries(summoner, max_entries=3)
        except AttributeError:
            await ctx.send("Could not find champion, please check spelling!")
            return
        except APIError as exception:
            await Summoner.raise_exception(self, ctx, exception)
            return

        embed = discord.Embed(colour=0x1affa7)
        loop, overall_wins, overall_losses = 0, 0, 0
        top_champs = "{0}, {1} and {2}".format(top_champ[0].champion.name,
                                               top_champ[1].champion.name,
                                               top_champ[2].champion.name)

        # Fixes URL for champions with spaces in their name (i.e Lee Sin)
        if " " in top_champ[0].champion.name:
            url_champ_name = top_champ[0].champion.name.replace(" ", "")
            url = 'http://ddragon.leagueoflegends.com/cdn/7.3.3/img/champion/{}.png'.format(
                   url_champ_name)

        # Fixes URL for champions with an apostrophe in their name (i.e Vel'Koz)
        # However the capitalisation is not standardised thus they have to be edited manually
        elif "Vel'Koz" in top_champ[0].champion.name:
            url = 'http://ddragon.leagueoflegends.com/cdn/7.3.3/img/champion/Velkoz.png'
        elif "Kha'Zix" in top_champ[0].champion.name:
            url = 'http://ddragon.leagueoflegends.com/cdn/7.3.3/img/champion/Khazix.png'
        elif "Rek'Sai" in top_champ[0].champion.name:
            url = 'http://ddragon.leagueoflegends.com/cdn/7.3.3/img/champion/RekSai.png'
        elif "Cho'Gath" in top_champ[0].champion.name:
            url = 'http://ddragon.leagueoflegends.com/cdn/7.8.1/img/champion/Chogath.png'
        elif "Kog'Maw" in top_champ[0].champion.name:
            url = 'http://ddragon.leagueoflegends.com/cdn/7.8.1/img/champion/KogMaw.png'
        else:
            url = 'http://ddragon.leagueoflegends.com/cdn/7.3.3/img/champion/{}.png'.format(
                   top_champ[0].champion.name)

        for league in leagues:
            loop += 1
            queue = league.queue.value
            tier = league.tier.value
            for entries in league.entries:
                division = entries.division.value
                league_points = str(entries.league_points) + ' LP'
                wins = entries.wins
                losses = entries.losses
                overall_wins += wins
                overall_losses += losses
                ratio = (wins / (wins + losses) * 100)

            if queue == 'RANKED_SOLO_5x5':
                embed.add_field(name="Ranked Solo:", value=u'\u200B', inline=True)
                embed.add_field(name="Division",
                                value="{0} {1} - {2}".format(tier, division, league_points),
                                inline=True)
                embed.add_field(name="W/L",
                                value="{0}W - {1}L ({2:.0F}%)".format(wins, losses, ratio),
                                inline=True)
            elif queue == 'RANKED_FLEX_SR':
                embed.add_field(name="Ranked Flex:", value=u'\u200B', inline=True)
                embed.add_field(name="Division",
                                value="{0} {1} - {2}".format(tier, division, league_points),
                                inline=True)
                embed.add_field(name="W/L",
                                value="{0}W - {1}L ({2:.0F}%)".format(wins, losses, ratio),
                                inline=True)
            elif queue == 'RANKED_FLEX_TT':
                embed.add_field(name="Ranked TT:", value=u'\u200B', inline=True)
                embed.add_field(name="Division",
                                value="{0} {1} - {2}".format(tier, division, league_points),
                                inline=True)
                embed.add_field(name="W/L",
                                value="{0}W - {1}L ({2:.0F}%)".format(wins, losses, ratio),
                                inline=True)

            overall_ratio = (overall_wins / (overall_wins + overall_losses) * 100)

        value1 = "{0}W/{1}L ({2:.2f})%".format(overall_wins, overall_losses,
                                               overall_ratio)
        op_gg = "https://{0}.op.gg/summoner/userName={1}".format(region, sum_name)
        embed.set_author(name="Summoner Lookup - {0} ({1})".format(sum_name, region),
                         url=op_gg, icon_url=url)
        embed.add_field(name="Overall:", value=u'\u200B', inline=True)
        embed.add_field(name="Top Champions", value=top_champs, inline=True)
        embed.add_field(name="W/L", value=value1, inline=True)
        embed.set_footer(text="Requested by: {0}".format(ctx.author.name),
                         icon_url=ctx.author.avatar_url)

        await ctx.send("", embed=embed)


def setup(bot):
    bot.add_cog(Summoner(bot))

    # TODO: SQL DB for default region per server.
    # Migrating V1 to dpy rewrite
    # More commands from API
    # Better formatting of final embed