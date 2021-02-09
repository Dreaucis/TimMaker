import random
import os

from pathlib import Path
from discord.ext import commands

bot = commands.Bot(command_prefix='$')

TEAM_NAME_ADJECTIVES = [
    'Electrifying',
    'Exhilarating',
    'Delightful',
    'Sensational',
    'Animating',
    'Stimulating',
    'Vitalizing',
    'Overjoyed',
    'Euphoric',
    'Jubilant',
    'Cool',
    'Smart'
]

TEAM_NAME_ANIMALS = [
    'Moose (Meese? Mooses?) :thinking:',
    'Ducks',
    'Tigers',
    'Elephants',
    'Silverfishes',
    'Cats',
    'Penguins',
    'Squirrels',
    'Hedgehogs',
    'Dogs',
    'Pandas',
    'Rabbits',
    'Donkeys'
]


@bot.command()
async def make_tim(ctx: commands.Context, *extra_players, number_of_teams=2, voice_channel_nr=0):
    """ Divides the users in the channel into teams """
    voice_channel = ctx.guild.voice_channels[voice_channel_nr]
    users = [m.name for m in voice_channel.members] + list(extra_players)
    users = random.sample(users, len(users))

    if len(users) < 2:
        msg = """
            I, Tim, can only see {N_USERS} in the voice channel {VOICE_CHN_NAME}. If you are more than that in the voice 
            channel, then leaving and joining again is likely to fix it!
            """.format(N_USERS=len(users), VOICE_CHN_NAME=voice_channel.name)
        await ctx.channel.send(msg)
        return

    teams = [[] for i in range(number_of_teams)]
    for i, user in enumerate(users):
        teams[i % number_of_teams].append(user)

    msg = 'I, Tim, made these tims!:\n'
    team_name_adjectives = random.sample(TEAM_NAME_ADJECTIVES, number_of_teams)
    team_name_animals = random.sample(TEAM_NAME_ANIMALS, number_of_teams)
    for i, team in enumerate(teams):
        msg += 'The {ADJECTIVE} {ANIMAL} \n'.format(ADJECTIVE=team_name_adjectives[i], ANIMAL=team_name_animals[i])
        msg += '\t {TEAM_MEMBERS}\n'.format(TEAM_MEMBERS=str(team).strip("[]").replace("'", ''))
    msg += 'GL HF!'

    await ctx.channel.send(msg)


def get_token_from_file(file: Path):
    with file.open() as f:
        return f.read().split('=')[1]


bot.run(os.getenv('TOKEN') or get_token_from_file(Path(__file__).parent / '.env'))
