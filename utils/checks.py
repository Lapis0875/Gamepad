from typing import Final

from discord.ext import commands

__all__ = (
    'is_owner',
    'checkInVoice'
)


OWNER_ID: Final[int] = 280855156608860160       # It's me, Lapis!


async def is_owner(ctx: commands.Context):
    """
    Check if command is used by bot's owner.
    :param ctx: Command context.
    :return: If command's user is bot's owner.
    """
    return ctx.author.id == OWNER_ID


async def checkInVoice(ctx: commands.Context):
    if not ctx.author.voice:
        await ctx.send('통화방에 참여해 있어야 실행할 수 있습니다 :(')
        return False
    return True