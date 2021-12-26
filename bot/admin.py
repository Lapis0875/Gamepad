import asyncio
from functools import partial, wraps
from typing import Final, Callable

from discord import Cog, slash_command, ApplicationContext, Embed, ui, ButtonStyle, Interaction

from bot.constants import INITIAL_COLOR, ADMIN_ID, TEST_SERVERS
from bot.gamepad_bot import GamepadBot
from typings import CoroutineFunction


class AdminButton(ui.Button):
    def __init__(self, msg_id, callback: CoroutineFunction, style: ButtonStyle, custom_id: str, label: str = None, emoji: str = None):
        super(AdminButton, self).__init__(style=style, custom_id=custom_id, label=label, emoji=emoji)
        self.callback = AdminButton.wrap_callback(self, callback)
        self.msg_id = msg_id

    @staticmethod
    def wrap_callback(self, coro: CoroutineFunction):
        callback = partial(coro, self)
        return callback

    @classmethod
    def create(cls, msg_id: int, style: ButtonStyle, suffix: str, label: str = None, emoji: str = None) -> Callable[[CoroutineFunction], 'AdminButton']:
        def wrapper(coro: CoroutineFunction) -> AdminButton:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError('Callback function of AdminButton must be a coroutine function.')
            return cls(msg_id, coro, style, 'admin_' + str(msg_id) + suffix, label, emoji)

        return wrapper


def admin_check(coro: CoroutineFunction) -> CoroutineFunction:
    """
    Wraps callback function to ensure work for only admins.
    :param coro: callback function to add check.
    """
    @wraps(coro)
    async def wrapper(self: ui.Button, interaction: Interaction):
        if interaction.user.id != ADMIN_ID:
            return await interaction.response.send_message('당신은 관리자가 아닙니다.', ephemeral=True, delete_after=3.0)
        return await coro(self, interaction)
    return wrapper


class AdminView(ui.View):
    def __init__(self, msg_id, bot: GamepadBot):
        self.index = 0
        self.bot: GamepadBot = bot

        @AdminButton.create(msg_id=msg_id, style=ButtonStyle.danger, suffix='_stop', label='종료', emoji='⛔')
        @admin_check
        async def stop_btn(self: ui.Button, interaction: Interaction):
            await interaction.response.send_message('잠시 후 봇이 종료됩니다.', ephemeral=True, delete_after=3.0)
            await self.view.bot.close()

        self.stop_btn = stop_btn

        @AdminButton.create(msg_id=msg_id, style=ButtonStyle.primary, suffix='_exit', label='나가기', emoji='❌')
        @admin_check
        async def exit_btn(self: ui.Button, interaction: Interaction):
            await interaction.response.send_message('관리 패널을 종료합니다.', ephemeral=True, delete_after=3.0)
            self.view.stop()
            await interaction.message.delete()

        self.exit_btn = exit_btn

        super(AdminView, self).__init__(self.stop_btn, self.exit_btn, timeout=120)


class GamepadHelp(Cog, name='admin'):
    def __init__(self, bot: GamepadBot):
        self.bot = bot

    def cog_unload(self) -> None:
        """
        Handle cog unload.
        """

    @slash_command(name='admin', description='관리자 명령어입니다.', guild_ids=TEST_SERVERS)
    async def admin_slash(self, ctx: ApplicationContext):
        if ctx.author.id != ADMIN_ID:
            return await ctx.response.send_message('관리자만 사용 가능합니다!', ephemeral=True, delete_after=3.0)
        embed = Embed(
            title='Gamepad 관리 🕹️',
            color=INITIAL_COLOR
        )
        await ctx.response.send_message(embed=embed, view=AdminView(ctx.guild_id, self.bot))


def setup(bot: GamepadBot):
    bot.add_cog(GamepadHelp(bot))
    bot.logger.info('관리 기능을 활성화했습니다.')


def teardown(bot: GamepadBot):
    bot.remove_cog('admin')
    bot.logger.info('관리 기능을 비활성화했습니다.')
