import asyncio
from functools import partial
from typing import Final, Callable

from discord import Cog, slash_command, ApplicationContext, Embed, ui, ButtonStyle, Interaction

from bot.constants import INITIAL_COLOR, TEST_SERVERS
from bot.gamepad_bot import GamepadBot
from typings import CoroutineFunction

HELP_TEXTS: Final[list[tuple[str, str]]] = [
    ('LFG 생성', 'lfg를 새롭게 생성합니다. lfg를 생성한 사람은 기본적으로 lfg에 참여한 상태가 됩니다.\n\n'
               '`/lfg create {name} {description} {game} {dt}` 로 사용할 수 있습니다.\nㅤ',),
    ('LFG 편집', '기존 lfg를 편집합니다.\n\n'
               '`/lfg edit {id}` 로 사용할 수 있습니다.\nㅤ'),
    ('LFG 삭제', '기존 lfg를 삭제합니다. lfg를 생성한 사람 본인만 가능합니다.\n\n'
               '`/lfg delete {id}` 로 사용할 수 있습니다.\nㅤ'),
    ('LFG 보기', 'id에 해당하는 lfg를 보여줍니다.\n\n'
               '`/lfg view {id}` 로 사용할 수 있습니다.\nㅤ'),
    ('LFG 목록 보기', '생성된 lfg의 목록을 확인합니다. 전체 lfg 목록과, 자신이 생성한 lfg의 목록을 보여줍니다.\n\n'
                  '`/lfg list` 로 사용할 수 있습니다.\nㅤ')
]

HELP_LENGTH: Final[int] = len(HELP_TEXTS)
HELP_EMBEDS: Final[list[Embed]] = [
    Embed(
        title='Gamepad 도움말 🎮',
        color=INITIAL_COLOR
    ).add_field(
        name=name,
        value=value,
        inline=False
    ) for name, value in HELP_TEXTS
]


class HelpButton(ui.Button):
    def __init__(self, msg_id, callback: CoroutineFunction, emoji: str, custom_id: str):
        super(HelpButton, self).__init__(emoji=emoji, style=ButtonStyle.primary, custom_id=custom_id)
        self.callback = HelpButton.wrap_callback(self, callback)
        self.msg_id = msg_id

    @staticmethod
    def wrap_callback(self, coro: CoroutineFunction):
        callback = partial(coro, self)
        return callback

    @classmethod
    def create(cls, msg_id: int, emoji: str, suffix: str) -> Callable[[CoroutineFunction], 'HelpButton']:
        def wrapper(coro: CoroutineFunction) -> HelpButton:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError('Callback function of HelpButton must be a coroutine function.')
            return cls(msg_id, coro, emoji, 'help_' + str(msg_id) + suffix)

        return wrapper


class HelpView(ui.View):
    def __init__(self, msg_id):
        self.index = 0

        @HelpButton.create(msg_id=msg_id, emoji='◀️', suffix='_prev')
        async def prev_btn(btn: ui.Button, interaction: Interaction):
            if btn.view.index == len(HELP_EMBEDS):
                return await interaction.response.send_message('첫번째 페이지입니다.', ephemeral=True, delete_after=3.0)
            btn.view.index -= 1
            await interaction.edit_original_message(embed=HELP_EMBEDS[btn.view.index])

        self.prev_btn = prev_btn

        @HelpButton.create(msg_id=msg_id, emoji='▶️', suffix='_next')
        async def next_btn(btn: ui.Button, interaction: Interaction):
            if btn.view.index == HELP_LENGTH:
                return await interaction.response.send_message('마지막 페이지입니다.', ephemeral=True, delete_after=3.0)
            btn.view.index += 1
            await interaction.edit_original_message(embed=HELP_EMBEDS[btn.view.index])

        self.next_btn = next_btn

        super(HelpView, self).__init__(self.prev_btn, self.next_btn, timeout=120)


class GamepadHelp(Cog, name='help'):
    def __init__(self, bot: GamepadBot):
        self.bot = bot

    def cog_unload(self) -> None:
        """
        Handle cog unload.
        """

    @slash_command(name='help', description='도움말 명령어입니다.', guild_ids=TEST_SERVERS)
    async def help_slash(self, ctx: ApplicationContext):
        embed = Embed(
            title='Gamepad 도움말 🎮',
            color=INITIAL_COLOR
        )
        for name, value in HELP_TEXTS:
            embed.add_field(name=name, value=value, inline=False)
        embed.add_field(name='봇 코드', value='https://github.com/Lapis0875/Gamepad', inline=False)
        await ctx.response.send_message(embed=embed)


def setup(bot: GamepadBot):
    bot.add_cog(GamepadHelp(bot))
    bot.logger.info('도움말 기능을 활성화했습니다.')


def teardown(bot: GamepadBot):
    bot.remove_cog('help')
    bot.logger.info('도움말 기능을 비활성화했습니다.')
