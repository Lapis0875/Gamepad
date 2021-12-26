import traceback

import discord
from discord.ext import commands
from .colors import *

__all__ = (
    'EmbedPresets',
)


class EmbedPresets:
    def __new__(cls, *args, **kwargs):
        raise TypeError('Cannot create instance of namespace classes!')

    @classmethod
    def greeting_embed(cls) -> discord.Embed:
        return discord.Embed(
            colour=PantoneColors.Yellow012C,
            title='별무리 봇 온라인 ☀',
            description='별무리 서버 - v1.0'
        )

    @classmethod
    def close_embed(cls) -> discord.Embed:
        return discord.Embed(
            colour=PantoneColors.DarkBlueC,
            title='별무리 봇을 종료합니다... 🪐',
            description='별무리 서버 - v1.0'
        )

    @classmethod
    def restart_embed(cls) -> discord.Embed:
        return discord.Embed(
            colour=discord.Colour.orange(),
            title='별무리 봇을 재시작합니다! 🌌',
            description='별무리 서버 - v1.0'
        )

    @classmethod
    def game_roles_embed(cls) -> discord.Embed:
        return discord.Embed(
            colour=PantoneColors.StarSapphire,
            title='별무리 서버 > 게임 역할',
            description='아래 이모지를 눌러 게임 역할을 지급받으세요!'
        )

    @classmethod
    def info_embed(cls, title: str, description: str) -> discord.Embed:
        return discord.Embed(
            color=PantoneColors.StarSapphire,
            title=title,
            description=description
        )

    @classmethod
    def warn_embed(cls, title: str, description: str) -> discord.Embed:
        return discord.Embed(
            title=title,
            description=description,
            colour=PantoneColors.Yellow012C
        )

    @classmethod
    def error_embed(cls, title: str, description: str) -> discord.Embed:
        return discord.Embed(
            colour=discord.Colour.red(),
            title=title,
            description=description
        )

    @classmethod
    def error_embed_with_traceback(cls, title: str, description: str, error: Exception) -> discord.Embed:
        e = discord.Embed(
            color=discord.Color.dark_red(),
            title=title,
            description=description
        )
        e.add_field(
            name='Exception',
            value=str(error),
            inline=True
        )
        e.add_field(
            name='Tracebacks:',
            value='Fields below.',
            inline=True
        )
        for i, tb in enumerate(traceback.extract_tb(error.__traceback__).format()):
            e.add_field(
                name=f'**[{i}]** Traceback',
                value=tb,
                inline=False
            )

        if isinstance(error, commands.CommandInvokeError):
            e.add_field(
                name=f'Original Exception Info',
                value=f'{error.original.__class__}: {error.original}',
                inline=False
            )
            for i, tb in enumerate(traceback.extract_tb(error.original.__traceback__).format()):
                e.add_field(
                    name=f'**[{i}]** Original Traceback',
                    value=tb,
                    inline=False
                )

        return e
