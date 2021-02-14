#!/usr/bin/python3
import random
import os

from pathlib import Path
from functools import lru_cache
from typing import Optional, List
from asyncio import TimeoutError

import requests
from discord.ext import commands
from constants import MSG_DELETION_TIME, SUGGEST_HERO_SENTENCES, SUGGEST_TEAM_ADJECTIVES, SUGGEST_TEAM_ANIMALS, \
    HERO_ROLES

bot = commands.Bot(command_prefix='$')


@lru_cache(maxsize=128)
def get_hero_list(role: Optional[str] = None) -> List[str]:
    """
    Queries the HeroesProfile open API for a list of heroes. Returns a list of hero names.

    Args:
         role: Optional; Limit the query by specifying what role the hero should have

    Returns:
        A list of hero names.

    """
    if role:
        r = requests.get('https://api.heroesprofile.com/openApi/Heroes', {'role': role})
    else:
        r = requests.get('https://api.heroesprofile.com/openApi/Heroes')
    return list(r.json())


def get_token_from_file(file: Path) -> str:
    """ Naively parse a file for a token. Expects the format to be <TOKEN_NAME>=<TOKEN>."""
    with file.open() as f:
        return f.read().split('=')[1]


def assign_teams(users: List[str], number_of_teams: int) -> List[List[str]]:
    """ Randomly splits users into <number_of_teams> lists """
    users = random.sample(users, len(users))  # Shuffle to ensure different teams
    teams = [[] for _ in range(number_of_teams)]
    for i, user in enumerate(users):
        teams[i % number_of_teams].append(user)
    return teams


def construct_suggest_team_reply(teams: List[List[str]], adjectives: List[str], animals: List[str]) -> str:
    """ Constructs the message for suggesting teams """
    msg = 'I, Tim, suggest these teams!:\n'
    for i, team in enumerate(teams):
        msg += 'The {ADJECTIVE} {ANIMAL} \n'.format(ADJECTIVE=adjectives[i], ANIMAL=animals[i])
        msg += '\t {TEAM_MEMBERS}\n'.format(TEAM_MEMBERS=str(team).strip("[]").replace("'", ''))
    msg += 'GL HF!'
    return msg


@bot.command()
async def suggest_teams(ctx: commands.Context, *extra_players: str):
    """
    Randomly divides users in the first voice channel into teams. Additional users can be added by typing their names
    separated by spaces.

    Buttons:
        🔄: Redraft the teams

    Example:
        $suggest_teams
        $suggest_teams Player1 Player2
    """
    number_of_teams = 2  # The number of teams
    voice_channel_nr = 0  # The voice channel to find users in. 0 is the first top to down in Discord

    # Collect users in voice and args
    voice_channel = ctx.guild.voice_channels[voice_channel_nr]
    users = [m.name for m in voice_channel.members] + list(extra_players)

    # If there's are less than two users, then no teams can be constructed. Inform user and return.
    if len(users) < 2:
        msg = (
            "I, Tim, can only see {N_USERS} in the voice channel {VOICE_CHL_NAME}. "
            "If you are more than that in the voice channel, then leaving and joining again is likely to fix it!"
        ).format(N_USERS=len(users), VOICE_CHL_NAME=voice_channel.name)
        await ctx.channel.send(msg, delete_after=MSG_DELETION_TIME)
        return

    # Assign users to teams
    teams = assign_teams(users, number_of_teams)

    # Created random team names. Performed here to allow for the same names after redraft
    team_name_adjectives = random.sample(SUGGEST_TEAM_ADJECTIVES, len(teams))
    team_name_animals = random.sample(SUGGEST_TEAM_ANIMALS, len(teams))

    # Construct reply
    msg = construct_suggest_team_reply(teams, team_name_adjectives, team_name_animals)

    # Send first team lineup
    message = await ctx.channel.send(msg)

    # Add a redraft button
    redo_emoji = '🔄'
    await message.add_reaction(redo_emoji)

    # Wait for any redraft to be requested, if any are requested. Redraft the teams and print the new teams.
    while True:
        # Wait for the redraft emoji reaction. If none is given after <MSG_DELETION_TIME> sec delete message and return.
        try:
            reaction, user = await bot.wait_for(
                'reaction_add',
                timeout=MSG_DELETION_TIME,
                check=lambda r, u:  str(r.emoji) == redo_emoji and u != message.author
            )
        except TimeoutError:
            await message.delete()
            return

        await message.remove_reaction(reaction, user)  # Remove the new react to allow for multiple redrafts

        # Redraft teams abd reconstruct the message
        teams = assign_teams(users, number_of_teams)
        msg = construct_suggest_team_reply(teams, team_name_adjectives, team_name_animals)

        # Edit the message
        await message.edit(content=msg)


@bot.command()
async def suggest_hero(ctx: commands.Context, *, role: Optional[str] = None):
    """ 
    Randomly suggests a hero. The suggestions can be further specified down by role.
    
    Available roles include:
        Support
        Healer
        Bruiser
        Tank
        Melee assassin
        Ranged assassin

    Example:
        $suggest_hero
        $suggest_hero Bruiser
    """
    # If a role was specified but not found, inform the user and return
    if role and role.lower() not in HERO_ROLES:
        msg = (
            'Tim could not find any heroes with the role {ROLE}.\n'
            'Valid roles include: {ROLES}.'
        ).format(ROLE=role, ROLES=', '.join(HERO_ROLES))

        await ctx.channel.send(msg, delete_after=MSG_DELETION_TIME)
        return

    # Pick a random hero
    heroes = get_hero_list(role)
    hero = random.choice(heroes)

    # Construct reply
    sentences = [s.format(HERO=hero) for s in SUGGEST_HERO_SENTENCES]
    msg = random.choice(sentences)

    await ctx.channel.send(msg, delete_after=MSG_DELETION_TIME)


if __name__ == '__main__':
    bot.run(os.getenv('TOKEN') or get_token_from_file(Path(__file__).parent / '.env'))
