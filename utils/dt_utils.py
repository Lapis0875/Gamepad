import datetime
import pytz

from bot.constants import DAY2SEC

UTC = pytz.UTC
KST = pytz.timezone("Asia/Seoul")


def get_current_dt(tz: datetime.timezone = KST) -> datetime.datetime:
    utc_now = UTC.localize(datetime.datetime.utcnow())
    return utc_now.astimezone(tz)


def normalize_to_kst(dt: datetime.datetime) -> datetime.datetime:
    if dt.tzinfo is None:
        raise ValueError('Cannot normalize naive datetime!')

    return dt.astimezone(KST)


def text2dt(text: str, tz: datetime.timezone = KST) -> datetime.datetime:
    """
    Parse datetime text to datetime object.
    :param text: YYYY-MM-DD:HH-MM format datetime expression.
    :param tz: timezone of given datetime.
    :return:
    """
    text_split = text.split(':')
    if len(text_split) == 2:
        d, t = text_split
    else:
        tzname, d, t = text_split
        tz = pytz.timezone(tzname)
    return datetime.datetime(*map(int, d.split('-')), *map(int, t.split('-')), 0, 0, tzinfo=tz)


def dt2text(dt: datetime.datetime, tzname_default: str = 'Asia/Seoul') -> str:
    """
    Parse datetime text to datetime object.
    :param dt: datetime object to parse.
    :return: tz:YYYY-MM-DD:HH-MM format datetime expression.
    """
    return f'{str(dt.tzinfo)}:{dt.year}-{dt.month}-{dt.day}:{dt.hour}-{dt.minute}'


def readable_time_text(dt: datetime.datetime) -> str:
    return f'{dt.year}년 {dt.month}월 {dt.day}일 {dt.hour}시 {dt.minute}분'


def timedelta2sec(td: datetime.timedelta) -> int:
    return td.days * DAY2SEC + td.seconds
