import asyncio
import sqlite3
from datetime import datetime, timedelta
from functools import partial
from typing import Callable, Optional

import aiofiles
import aiosqlite
import attr
from discord import ui, commands, ButtonStyle, Interaction, Embed
from discord import Cog, Option, Guild, Member
from discord.ext import tasks

from typings import CoroutineFunction
from utils.asyncio_helper import async_schedule_task
from .constants import ADMIN_ID, DB_PATH, CREATE, EDIT, LIST, DELETE, INITIAL_COLOR, VIEW, TEST_SERVERS, \
    LFG_ALERT_PREV_SEC, DUMP_PATH
from .gamepad_bot import GamepadBot
from utils.dt_utils import text2dt, dt2text, readable_time_text, get_current_dt, timedelta2sec


# from .slash_patch import lazy_group_creation


@attr.s(init=True, repr=True, cmp=True)
class LFG:
    """
    LFG model object.
    """
    # Bot instance that created this lfg.
    bot = attr.ib(type=GamepadBot, init=True, repr=False, cmp=False)

    # LFG Info
    id = attr.ib(type=int, init=True, repr=True, cmp=True)
    name = attr.ib(type=str, init=True, repr=True, cmp=False)
    description = attr.ib(type=str, init=True, repr=False, cmp=False)
    game = attr.ib(type=str, init=True, repr=True, cmp=False)
    dt = attr.ib(type=datetime, init=True, repr=False, cmp=False)

    # Discord-Related
    guild = attr.ib(type=Guild, init=True, repr=False, cmp=False)
    owner = attr.ib(type=Member, init=True, repr=False, cmp=False)

    # Member List
    participants = attr.ib(type=list, init=False, default=attr.Factory(list))
    alternatives = attr.ib(type=list, init=False, default=attr.Factory(list))

    # Scheduled object
    _task = attr.ib(type=asyncio.Task, init=False, repr=False, cmp=False, default=None)

    def add_participant(self, member: Member):
        """
        Add member to lfg.
        :param member:
        """
        self.participants.append(member)

    def remove_participant(self, member: Member):
        self.participants.remove(member)

    def remove_participant_by_id(self, member_id: int):
        member = next(filter(lambda m: m.id == member_id, self.participants), None)
        self.participants.remove(member)

    def has_participant(self, member: Member):
        return member in self.participants

    def has_participant_by_id(self, member_id: int):
        return any(filter(lambda m: m.id == member_id, self.participants))

    def add_alternative(self, member: Member):
        """
        Add member to lfg.
        :param member:
        """
        self.alternatives.append(member)

    def remove_alternative(self, member: Member):
        self.alternatives.remove(member)

    def remove_alternative_by_id(self, member_id: int):
        member = next(filter(lambda m: m.id == member_id, self.alternatives), None)
        self.alternatives.remove(member)

    def has_alternative(self, member: Member):
        return member in self.alternatives

    def has_alternative_by_id(self, member_id: int):
        return any(filter(lambda m: m.id == member_id, self.alternatives))

    async def update(self, name: str, description: str, game: str, dt: datetime):
        self.name = name
        self.description = description
        self.game = game
        self.dt = dt
        self._task.cancel('lfg 업데이트로 인한 예약 취소 및 다시 예약하기.')
        await self.schedule()

    async def alert_members(self):
        for m in self.participants:
            await m.send(embed=self.alert_embed())

    async def schedule(self):
        kst_now = get_current_dt()
        td_left: timedelta = self.dt - kst_now
        sec_left: int = timedelta2sec(td_left)
        if sec_left < LFG_ALERT_PREV_SEC:
            return await self.alert_members()
        else:
            self._task = async_schedule_task(sec_left, self.alert_members, None)

    @classmethod
    async def deserialize(
            cls,
            bot: GamepadBot,
            id: int,
            name: str,
            description: str,
            game: str,
            datetime_raw: str,
            guild_id: int,
            owner_id: int,
            participants_raw: str,
            alternatives_raw: str
    ) -> 'LFG':
        """
        Deserialize from db.
        :param bot: bot instance.
        :param id: id of lfg
        :param name: name of lfg
        :param description: description of lfg
        :param game: game title of lfg
        :param datetime_raw: raw text expression of datetime. (serialized using dt2text)
        :param guild_id: id of guild
        :param owner_id: id of member who created this lfg.
        :param participants_raw: raw text of participants' member ids separated using ',' char.
        :param alternatives_raw: raw text of alternatives' ids separated using ',' char.
        :return: LFG instance.
        """
        dt = text2dt(datetime_raw)
        guild = bot.get_guild(guild_id) or (await bot.fetch_guild(guild_id))
        owner = guild.get_member(owner_id) or (await guild.fetch_member(owner_id))
        lfg = cls(bot, id, name, description, game, dt, guild, owner)
        if participants_raw != '':  # Not empty.
            for member_id in map(int, participants_raw.split(',')):
                member = guild.get_member(member_id) or (await guild.fetch_member(member_id))
                lfg.add_participant(member)
        if alternatives_raw != '':  # Not empty.
            for member_id in map(int, alternatives_raw.split(',')):
                member = guild.get_member(member_id) or (await guild.fetch_member(member_id))
                lfg.add_alternative(member)

        return lfg

    def serialize(self) -> tuple[str, str, str, str, int, int, str, str, int]:
        """
        Serialize to write in db.
        :return: tuple of raw values (id: int, name: str, description: str, datetime: datetime -> str, participants: list -> str)
        """
        return (
            self.name,
            self.description,
            self.game,
            dt2text(self.dt),
            self.guild.id,
            self.owner.id,
            ','.join(map(lambda m: str(m.id), self.participants)),
            ','.join(map(lambda m: str(m.id), self.alternatives)),
            self.id
        )

    def view(self) -> 'LFGView':
        return LFGView(self)

    def info_embed(self) -> Embed:
        return Embed(
            title=f'LFG : {self.name}',
            description=self.description,
            color=INITIAL_COLOR
        ).add_field(
            name='id',
            value=self.id,
            inline=True
        ).add_field(
            name='예정 시각',
            value=readable_time_text(self.dt),
            inline=True
        ).add_field(
            name='게임',
            value=self.game,
            inline=False
        ).add_field(
            name=f'참여자 ({len(self.participants)})',
            value=', '.join(map(lambda m: m.display_name, self.participants)) if len(self.participants) > 0 else 'ㅤ',
            inline=False
        ).add_field(
            name=f'고민중 ({len(self.alternatives)})',
            value=', '.join(map(lambda m: m.display_name, self.alternatives)) if len(self.alternatives) > 0 else 'ㅤ',
            inline=True
        ).set_author(
            name=self.owner.display_name,
            # icon_url=self.owner.display_avatar.url
        )

    def alert_embed(self) -> Embed:
        self.bot.logger.info(
            '\n'.format(map(lambda m: f'- ({type(m)}) {m.display_name}#{m.discriminator}', self.participants)))
        return Embed(
            title=f'LFG : {self.name}',
            description='lfg 예정 시간이 얼마 남지 않았습니다.',
            color=INITIAL_COLOR
        ).add_field(
            name='참여자',
            value=', '.join(map(lambda m: m.display_name, self.participants)) if len(self.participants) > 0 else 'ㅤ',
            inline=False
        ).set_author(
            name=self.owner.display_name,
            # icon_url=self.owner.display_avatar.url
        ).set_thumbnail(
            url=self.guild.icon.url
        )


class LFGButton(ui.Button):
    def __init__(self, lfg, callback: CoroutineFunction, label: str, style: ButtonStyle, custom_id: str):
        super(LFGButton, self).__init__(label=label, style=style, custom_id=custom_id)
        self.callback = LFGButton.wrap_callback(self, callback)
        self.lfg = lfg

    @staticmethod
    def wrap_callback(self, coro: CoroutineFunction):
        callback = partial(coro, self)
        return callback

    @classmethod
    def assign_lfg(cls, lfg: LFG, label: str, style: ButtonStyle, suffix: str) -> Callable[[CoroutineFunction], 'LFGButton']:
        def wrapper(coro: CoroutineFunction) -> LFGButton:
            if not asyncio.iscoroutinefunction(coro):
                raise TypeError('Callback function of LFGButton must be a coroutine function.')
            return cls(lfg, coro, label, style, str(lfg.id) + suffix)

        return wrapper


class LFGView(ui.View):
    async def update_lfg_embed(self, interaction: Interaction):
        """
        Update embed in interaction response to apply changes in lfg.
        :param interaction: interaction payload.
        """
        await interaction.response.edit_message(embed=self.lfg.info_embed())

    def __init__(self, lfg: LFG):
        self.lfg = lfg

        @LFGButton.assign_lfg(lfg, '+', ButtonStyle.success, '_join')
        async def join_btn(btn: LFGButton, interaction: Interaction):
            if not lfg.has_participant_by_id(interaction.user.id):
                if lfg.has_alternative_by_id(interaction.user.id):
                    lfg.remove_alternative_by_id(interaction.user.id)
                lfg.add_participant(interaction.user)
            else:
                return await interaction.response.send_message(content='이미 참여하셨습니다!', ephemeral=True, delete_after=3.0)
            await btn.view.update_lfg_embed(interaction)

        self.join_btn = join_btn

        @LFGButton.assign_lfg(lfg, '?', ButtonStyle.primary, '_alt')
        async def alt_btn(btn: LFGButton, interaction: Interaction):
            if not lfg.has_alternative_by_id(interaction.user.id):
                if lfg.has_participant_by_id(interaction.user.id):
                    lfg.remove_participant_by_id(interaction.user.id)
                lfg.add_alternative(interaction.user)
            else:
                return await interaction.response.send_message(content='이미 참여하셨습니다!', ephemeral=True, delete_after=3.0)
            await btn.view.update_lfg_embed(interaction)

        self.alt_btn = alt_btn

        @LFGButton.assign_lfg(lfg, '-', ButtonStyle.danger, '_leave')
        async def leave_btn(btn: LFGButton, interaction: Interaction):
            if lfg.has_participant_by_id(interaction.user.id):
                lfg.remove_participant(interaction.user)
            elif lfg.has_alternative_by_id(interaction.user.id):
                lfg.remove_alternative(interaction.user)
            else:
                return await interaction.response.send_message(content='lfg에 참여하지 않으셨습니다!', ephemeral=True, delete_after=3.0)
            await btn.view.update_lfg_embed(interaction)

        self.leave_btn = leave_btn
        super(LFGView, self).__init__(self.join_btn, self.alt_btn, self.leave_btn,
                                      timeout=0)  # set timeout 0 to respond anytime.


class GamepadLFG(Cog, name='lfg'):
    def __init__(self, bot: GamepadBot):
        self.bot = bot
        self.lfg_cache: list[LFG] = []
        self.bot.loop.create_task(self.fetch_db(), name='lfg.fetch')
        self.lfg_group = bot.create_group('lfg', 'LFG 명령어', guild_ids=TEST_SERVERS)

        self.lfg_group.command(name=CREATE, description='LFG를 생성합니다.')(self.lfg_create)
        self.lfg_group.command(name=EDIT, description='LFG를 편집합니다.')(self.lfg_edit)
        self.lfg_group.command(name=LIST, description='생성된 LFG의 목록을 확인합니다.')(self.lfg_list)
        self.lfg_group.command(name=DELETE, description='LFG를 삭제합니다.')(self.lfg_delete)
        self.lfg_group.command(name=VIEW, description='LFG 정보를 표시합니다.')(self.lfg_view)
        self.lfg_group.command(name='commit', description='LFG 데이터를 저장합니다.')(self.lfg_manual_save)

    def cog_unload(self) -> None:
        """
        Handle cog unload.
        """
        self.bot.loop.create_task(self.save_db(), name='lfg.commit')

    # DB Operations
    @tasks.loop(hours=1)
    async def backup_db(self):
        self.bot.logger.info('Start database dump.')
        async with aiosqlite.connect(DB_PATH) as conn:
            async with aiofiles.open(DUMP_PATH, mode='w') as f:
                async for line in conn.iterdump():
                    await f.write(line + '\n')
        self.bot.logger.info('Database dump completed.')

    # DB Operations
    @tasks.loop(hours=1)
    async def save_db_task(self):
        await self.save_db()

    async def fetch_db(self):
        async with aiosqlite.connect(DB_PATH) as con:
            # For first startup.
            await con.execute('CREATE TABLE IF NOT EXISTS lfg '
                              '(id INTEGER PRIMARY KEY, '
                              'name TEXT NOT NULL, '
                              'description TEXT, '
                              'game TEXT, '
                              'datetime TEXT, '
                              'guild INTEGER, '
                              'owner INTEGER, '
                              'participants TEXT, '
                              'alternatives TEXT)')
            # get all lfg
            lfg_cache: list[LFG] = []
            async with con.execute('SELECT * FROM lfg') as c:
                async for col in c:
                    lfg_cache.append(await LFG.deserialize(self.bot, *col))
            self.lfg_cache = lfg_cache

    async def save_db(self):
        self.bot.logger.info('Saving current lfg.')
        if len(self.lfg_cache) == 0:
            self.bot.logger.info('No lfg on memory. Cancel save.')
            return
        async with aiosqlite.connect(DB_PATH) as conn:
            async with conn.cursor() as cur:
                for lfg in self.lfg_cache:
                    try:
                        await cur.execute(
                            'INSERT INTO lfg VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            lfg.serialize()
                        )
                    except sqlite3.IntegrityError:
                        await cur.execute(
                            'UPDATE lfg SET '
                            'name=?, '
                            'description=?, '
                            'game=?, '
                            'datetime=?, '
                            'guild=?, '
                            'owner=?, '
                            'participants=?, '
                            'alternatives=? '
                            'WHERE id = ?',
                            lfg.serialize()
                        )
                # await cur.executemany(
                #     'INSERT INTO lfg VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                #     map(lambda lfg: lfg.serialize(), self.lfg_cache)
                # )
            await conn.commit()
        self.bot.logger.info('Successfully saved current lfg data.')

    # LFG Operation
    def create_new_lfg(self, name: str, description: str, game: str, dt: datetime, guild: Guild, owner: Member):
        id: int = self.lfg_cache[-1].id + 1 if len(self.lfg_cache) > 0 else 0
        lfg = LFG(self.bot, id, name, description, game, dt, guild, owner)
        self.lfg_cache.append(lfg)
        return lfg

    # @slash_command(name='create', lazy_group='lfg')
    async def lfg_create(
            self,
            ctx: commands.ApplicationContext,
            name: Option(str, description='LFG의 이름입니다.'),
            description: Option(str, description='LFG의 설명입니다.'),
            game: Option(str, description='파티를 구하는 게임 이름입니다.'),
            dt: Option(str, description='LFG의 예정 시각입니다. YYYY-MM-DD:HH-MM 형식으로 입력해주세요.')
    ):
        """
        LFG Create slash command.
        :param ctx: ApplicationContext object.
        :param name: name of lfg.
        :param description: description of lfg.
        :param game: game title of lfg.
        :param dt: planned datetime of lfg.
        """
        try:
            dt = text2dt(dt)
        except Exception:
            return await ctx.respond('시간 형식이 잘못되었습니다.')
        lfg = self.create_new_lfg(name, description, game, dt, ctx.guild or None, ctx.author)
        lfg.add_participant(ctx.author)
        await lfg.schedule()
        await ctx.respond(embed=lfg.info_embed(), view=lfg.view())

    async def lfg_edit(
            self,
            ctx: commands.ApplicationContext,
            id: Option(int, 'LFG의 id입니다.')
    ):
        """
        LFG Edit slash command.
        :param ctx:
        :param id:
        """
        lfg = next(filter(lambda l: l.id == id, self.lfg_cache), None)
        if lfg is None:
            return await ctx.respond(f'id가 {id}인 lfg를 발견하지 못했습니다. :(')
        await ctx.defer(ephemeral=True)

        args = []
        for question in (
                'lfg의 제목을 정해주세요.',
                'lfg의 설명을 정해주세요.',
                'lfg의 게임을 정해주세요.',
                'lfg의 출발 시각을 정해주세요. (YYYY-MM-DD:HH-MM 형식)',
        ):
            question_msg = await ctx.send(question)
            answer = await self.bot.wait_for(
                'message',
                check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel_id
            )
            args.append(answer.content)
            await question_msg.delete()
            await answer.delete()

        args[-1] = text2dt(args[-1])
        await lfg.update(*args)
        await ctx.respond(embed=lfg.info_embed(), view=lfg.view())

    async def lfg_list(
            self,
            ctx: commands.ApplicationContext
    ):
        """
        LFG list slash command.
        :param ctx:
        :return:
        """
        await ctx.defer(ephemeral=False)
        text: str = '**LFG 명단 (최근 lfg 20개)**\n'
        for lfg in tuple(filter(lambda l: l.guild.id == ctx.guild_id, self.lfg_cache))[-20:]:
            text += f'{lfg.id} : {lfg.name}\n'
        await ctx.followup.send(text, ephemeral=False)
        own_lfg_text: str = f'**{ctx.author.display_name} 님의 lfg(최대 20개)**\n'
        for lfg in tuple(
                filter(lambda l: l.owner.id == ctx.author.id and l.guild.id == ctx.guild_id, self.lfg_cache))[
                   -20:]:
            own_lfg_text += f'{lfg.id} : {lfg.name}\n'
        await ctx.followup.send(own_lfg_text, ephemeral=False)

    async def lfg_delete(
            self,
            ctx: commands.ApplicationContext,
            id: Option(int, description='LFG의 id입니다.')
    ):
        """
        LFG Delete slash command.
        :param ctx:
        :param id:
        :return:
        """
        lfg: Optional[LFG] = next(filter(lambda l: l.id == id, self.lfg_cache), None)
        if lfg is None:
            return await ctx.respond(f'id가 {id}인 lfg를 발견하지 못했습니다. :(', ephemeral=True)

        self.lfg_cache.remove(lfg)
        await ctx.respond(f'`{lfg.id} : {lfg.name}` lfg를 삭제했습니다.', ephemeral=True)

    async def lfg_view(
            self,
            ctx: commands.ApplicationContext,
            id: Option(int, description='lfg의 id입니다.')
    ):
        """
        LFG View slash command.
        :param ctx: ApplicationContext object.
        :param id: id of lfg.
        :return:
        """
        lfg: Optional[LFG] = next(filter(lambda l: l.id == id, self.lfg_cache), None)
        if lfg is None:
            return await ctx.respond(f'id가 {id}인 lfg를 발견하지 못했습니다. :(', ephemeral=True)
        await ctx.respond(embed=lfg.info_embed(), view=lfg.view())

    async def lfg_manual_save(self, ctx: commands.ApplicationContext):
        """
        Manually commit lfg data into db.
        :param ctx: ApplicationContext object.
        """
        if ctx.author.id != ADMIN_ID:
            return await ctx.response.send_message('관리자용 명령어입니다.', ephemeral=True, delete_after=3.0)
        try:
            await self.save_db()
        except sqlite3.OperationalError as e:
            return await ctx.respond(f'오류가 발생했습니다!\n{e}', ephemeral=True)
        await ctx.response.send_message('데이터베이스에 저장했습니다.')


def setup(bot: GamepadBot):
    # lfg_group, cog = lazy_group_creation(bot, GamepadLFG, name='lfg', description='LFG 기능.')
    cog = GamepadLFG(bot)
    bot.add_cog(cog)
    bot.logger.info('LFG 기능을 활성화했습니다.')


def teardown(bot: GamepadBot):
    bot.remove_cog('lfg')
    bot.logger.info('LFG 기능을 비활성화했습니다.')
