from discord import Cog, slash_command, Option

from bot.gamepad_bot import GamepadBot


class GamepadSNS(Cog, name='sns'):
    def __init__(self, bot: GamepadBot):
        self.bot = bot

    def cog_unload(self) -> None:
        """
        Handle cog unload.
        """

    @slash_command(name='register')
    async def sns_register(
            self,
            ctx,
            subcommand_opt: Option()
    ):
        pass


def setup(bot: GamepadBot):
    sns_group = bot.create_group(name='sns', description='SNS 명령어들입니다.')
    cog = GamepadSNS(bot)
    sns_group.add_application_command(cog.sns_register)
    bot.add_cog(cog)
    bot.logger.info('SNS 기능을 활성화했습니다.')


def teardown(bot: GamepadBot):
    bot.remove_cog('sns')
    bot.logger.info('SNS 기능을 비활성화했습니다.')
