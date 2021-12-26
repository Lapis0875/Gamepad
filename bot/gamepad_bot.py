from sys import stderr
from typing import Optional

from attr import attrs, attrib
from discord import Forbidden
from discord.ext.commands import Bot
from discord.utils import get, find
from orjson import loads

from bot.constants import DEFAULT_BOT_CONFIG_PATH
from typings.files import JSON
from utils.config import JsonConfig
from utils.log import get_logger


@attrs(init=True, repr=True)
class BotConfig(JsonConfig):
    """
    Config for bot.
    """
    token = attrib(type=str, repr=False)
    status_messages = attrib(type=list, default=[], repr=False)

    @classmethod
    def from_file(cls):
        with open(DEFAULT_BOT_CONFIG_PATH, mode='rt', encoding='utf-8') as f:
            config_dict: JSON = loads(f.read())     # speed up json load by using orjson
            return cls.from_json(config_dict)

    @classmethod
    def from_json(cls, json: JSON) -> 'BotConfig':
        return cls(
            path=DEFAULT_BOT_CONFIG_PATH,
            token=json['token'],
            status_messages=json['status_messages'],
        )


class GamepadBot(Bot):
    """
    Gamepad Discord Bot.
    """
    # async def register_commands(self) -> None:
    #     commands = []
    #
    #     # Global Command Permissions
    #     global_permissions: list = []
    #
    #     registered_commands = await self.http.get_global_commands(self.user.id)
    #
    #     if len(registered_commands) > 0:
    #         for command in filter(
    #             lambda c: c.guild_ids is None,
    #             self.pending_application_commands
    #         ):
    #             as_dict = command.to_dict()
    #             matching_registered_cmd: Optional[JSON] = next(filter(
    #                 lambda x: x["name"] == command.name and x["type"] == command.type,
    #                 registered_commands
    #             ), None)
    #             if matching_registered_cmd:
    #                 as_dict["id"] = matching_registered_cmd["id"]
    #             commands.append(as_dict)
    #
    #     cmds = await self.http.bulk_upsert_global_commands(self.user.id, commands)
    #
    #     for i in cmds:
    #         cmd = get(
    #             self.pending_application_commands,
    #             name=i["name"],
    #             guild_ids=None,
    #             type=i["type"],
    #         )
    #         cmd.id = i["id"]
    #         self._application_commands[cmd.id] = cmd
    #
    #         # Permissions (Roles will be converted to IDs just before Upsert for Global Commands)
    #         global_permissions.append({"id": i["id"], "permissions": cmd.permissions})
    #
    #     update_guild_commands = {}
    #     async for guild in self.fetch_guilds(limit=None):
    #         update_guild_commands[guild.id] = []
    #     for command in filter(
    #         lambda c: c.guild_ids is not None,
    #         self.pending_application_commands
    #     ):
    #         as_dict = command.to_dict()
    #         for guild_id in command.guild_ids:
    #             to_update = update_guild_commands[guild_id]
    #             to_update.append(as_dict)
    #
    #     for guild_id, guild_data in update_guild_commands.items():
    #         try:
    #             cmds = await self.http.bulk_upsert_guild_commands(
    #                 self.user.id, guild_id, update_guild_commands[guild_id]
    #             )
    #
    #             # Permissions for this Guild
    #             guild_permissions: list = []
    #         except Forbidden:
    #             if not guild_data:
    #                 continue
    #             print(f"Failed to add command to guild {guild_id}", file=sys.stderr)
    #             raise
    #         else:
    #             for i in cmds:
    #                 cmd = find(
    #                     lambda cmd: cmd.name == i["name"] and cmd.type == i["type"] and int(i["guild_id"]) in cmd.guild_ids,
    #                     self.pending_application_commands
    #                 )
    #                 cmd.id = i["id"]
    #                 self._application_commands[cmd.id] = cmd
    #
    #                 # Permissions
    #                 permissions = [
    #                     perm.to_dict()
    #                     for perm in cmd.permissions
    #                     if perm.guild_id is None
    #                     or (
    #                         perm.guild_id == guild_id and perm.guild_id in cmd.guild_ids
    #                     )
    #                 ]
    #                 guild_permissions.append(
    #                     {"id": i["id"], "permissions": permissions}
    #                 )
    #
    #             for global_command in global_permissions:
    #                 permissions = [
    #                     perm.to_dict()
    #                     for perm in global_command["permissions"]
    #                     if perm.guild_id is None
    #                     or (
    #                         perm.guild_id == guild_id and perm.guild_id in cmd.guild_ids
    #                     )
    #                 ]
    #                 guild_permissions.append(
    #                     {"id": global_command["id"], "permissions": permissions}
    #                 )
    #
    #             # Collect & Upsert Permissions for Each Guild
    #             # Command Permissions for this Guild
    #             guild_cmd_perms: list = []
    #
    #             # Loop through Commands Permissions available for this Guild
    #             for item in guild_permissions:
    #                 new_cmd_perm = {"id": item["id"], "permissions": []}
    #
    #                 # Replace Role / Owner Names with IDs
    #                 for permission in item["permissions"]:
    #                     if isinstance(permission["id"], str):
    #                         # Replace Role Names
    #                         if permission["type"] == 1:
    #                             role = get(
    #                                 self.get_guild(guild_id).roles,
    #                                 name=permission["id"],
    #                             )
    #
    #                             # If not missing
    #                             if role is not None:
    #                                 new_cmd_perm["permissions"].append(
    #                                     {
    #                                         "id": role.id,
    #                                         "type": 1,
    #                                         "permission": permission["permission"],
    #                                     }
    #                                 )
    #                             else:
    #                                 print(
    #                                     "No Role ID found in Guild ({guild_id}) for Role ({role})".format(
    #                                         guild_id=guild_id, role=permission["id"]
    #                                     )
    #                                 )
    #                         # Add owner IDs
    #                         elif (
    #                             permission["type"] == 2 and permission["id"] == "owner"
    #                         ):
    #                             app = await self.application_info()  # type: ignore
    #                             if app.team:
    #                                 for m in app.team.members:
    #                                     new_cmd_perm["permissions"].append(
    #                                         {
    #                                             "id": m.id,
    #                                             "type": 2,
    #                                             "permission": permission["permission"],
    #                                         }
    #                                     )
    #                             else:
    #                                 new_cmd_perm["permissions"].append(
    #                                     {
    #                                         "id": app.owner.id,
    #                                         "type": 2,
    #                                         "permission": permission["permission"],
    #                                     }
    #                                 )
    #                     # Add the rest
    #                     else:
    #                         new_cmd_perm["permissions"].append(permission)
    #
    #                 # Make sure we don't have over 10 overwrites
    #                 if len(new_cmd_perm["permissions"]) > 10:
    #                     print(
    #                         "Command '{name}' has more than 10 permission overrides in guild ({guild_id}).\nwill only use the first 10 permission overrides.".format(
    #                             name=self._application_commands[new_cmd_perm["id"]].name,
    #                             guild_id=guild_id,
    #                         )
    #                     )
    #                     new_cmd_perm["permissions"] = new_cmd_perm["permissions"][:10]
    #
    #                 # Append to guild_cmd_perms
    #                 guild_cmd_perms.append(new_cmd_perm)
    #
    #             # Upsert
    #             try:
    #                 await self.http.bulk_upsert_command_permissions(
    #                     self.user.id, guild_id, guild_cmd_perms
    #                 )
    #             except Forbidden:
    #                 print(
    #                     f"Failed to add command permissions to guild {guild_id}",
    #                     file=stderr,
    #                 )
    #                 raise

    async def sync_commands(self) -> None:
        self.add_application_command()
        print('Not Implemented!')
        raise NotImplementedError

    def __init__(self):
        self.config: BotConfig = BotConfig.from_file()
        self.logger = get_logger('gamepad')
        super(GamepadBot, self).__init__(command_prefix='<@923958493189398528>', help_command=None)

    def run(self, *args, **kwargs):
        """
        Run bot.
        * intent : To wrap original Bot.run() method to not receive any args and return restart flag.
        """
        self.load_extension('bot.lfg')
        # self.load_extension('bot.sns')
        self.load_extension('bot.help')
        self.load_extension('bot.admin')
        super(GamepadBot, self).run(self.config.token)

    async def on_ready(self):
        self.logger.info('봇이 실행되었습니다 :D')
        print('전체 슬래시 커맨드 :')
        for cmd in self.commands:
            print(f'{cmd.qualified_name()} : {id(cmd)} | parent : {cmd.parent.qualified_name() if cmd.parent is not None else "None"} ({id(cmd.parent)})')
        print('대기중인 슬래시 커맨드 :')
        for cmd in self.pending_application_commands:
            print(f'{cmd.qualified_name()} : {id(cmd)} | parent : {cmd.parent.qualified_name() if cmd.parent is not None else "None"} ({id(cmd.parent)})')
