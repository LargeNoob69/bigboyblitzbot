'''
Created on 15Jul.,2017

@author: Alex Palmer | SuperFrosty
'''
import config

from discord.ext import commands

DESCRIPTION = '''Op.gg but in your Discord lol'''

STARTUP_EXTENSIONS = ['utilities.utility_commands', 'summoner_stats', 'static_data', 'default_regions', 'reload',
                      'events']


class BlitzcrankBot(commands.AutoShardedBot):
    """Main"""

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('b!'), description=DESCRIPTION)
        self.bot_token = config.TOKEN
        self.api_key = config.API

        for extension in STARTUP_EXTENSIONS:
            try:
                self.load_extension(extension)
            except Exception as exception:
                exc = '{}: {}'.format(type(exception).__name__, exception)
                print('Failed to load extension {}\n{}'.format(extension, exc))

    async def on_message(self, message):
        pass

    def run(self):
        super().run(self.bot_token, reconnect=True)


if __name__ == '__main__':
    BlitzcrankBot().run()

# Base finished
