from typing import Type

from discord import Bot, Cog, SlashCommandGroup, SlashCommand


def lazy_group_creation(bot: Bot, cog_cls: Type[Cog], **kwargs) -> tuple[SlashCommandGroup, Cog]:
    """
    Lazy patch for slash group in Cogs.
    :param bot: discord.commands.Bot instance for slash commands.
    :param cog_cls: Cog's subclass to use slash group.
    :param kwargs: keyword-args to initialize SlashCommandGroup.
    :return: tuple of slash group & cog instance.
    """
    group = bot.create_group(**kwargs)
    cog_instance = cog_cls(bot)
    print(group.name, cog_instance.qualified_name)
    for slash in [cmd
                  for cmd in cog_instance.get_commands()
                  if isinstance(cmd, SlashCommand)
                  and cmd.__original_kwargs__.get('lazy_group') == group.name
                  ]:
        print(slash.name)
        slash.parent = group
        group.subcommands.append(slash)
    return group, cog_instance
