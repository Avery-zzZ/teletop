from typing import Callable, List
from argparse import ArgumentParser, Namespace
import shlex
import logging

from telethon.tl.custom.message import Message
from telethon.events.newmessage import NewMessage
from telethon.events.callbackquery import CallbackQuery
from telethon.tl.custom.button import Button

from app.core_service import CoreService

Event = NewMessage.Event | CallbackQuery.Event


def arg_hander(ap: ArgumentParser):
    def decorator(handle_func: Callable):
        async def wrapper(self: "AppService", event: Event, raw_command: str):
            try:
                parse_result = ap.parse_known_args(shlex.split(raw_command)[1:])
            except Exception as e:
                AppService.logger.info(f"args parse error: {e}")
                return await self.replyInvalidCommand(event)
            if len(parse_result[1]) > 0:
                return await self.replyInvalidCommand(event)
            else:
                return await handle_func(self, event, parse_result=parse_result)

        return wrapper

    return decorator


def no_arg_handler(handle_func: Callable):
    async def wrapper(self: "AppService", event: Event, raw_command: str):
        if len(shlex.split(raw_command)) != 1:
            return await self.replyInvalidCommand(event)
        else:
            return await handle_func(self, event)

    return wrapper


def chans_arg_handler(handle_func: Callable):
    async def wrapper(self: "AppService", event: Event, raw_command: str):
        @arg_hander(self.chans_args_parser)
        async def inner(
            self: "AppService",
            event: Event,
            parse_result: tuple[Namespace, list[str]],
        ):
            chans: list = parse_result[0].channels2
            chans.extend(parse_result[0].channels)
            if len(chans) == 0:
                return await self.replyInvalidCommand(event, "Please provide channels")
            else:
                return await handle_func(self, event, chans=chans)

        return await inner(self, event, raw_command)

    return wrapper


def top_arg_handler(handle_func: Callable):
    async def wrapper(self: "AppService", event: Event, raw_command: str):
        @arg_hander(self.top_args_parser)
        async def inner(
            self: "AppService",
            event: Event,
            parse_result: tuple[Namespace, list[str]],
        ):
            chan = None
            for i in [parse_result[0].channel2, parse_result[0].channel]:
                if i is not None:
                    if chan is not None:
                        return await self.replyInvalidCommand(
                            event, "Please provide only one channel"
                        )
                    chan = i
            if chan == None:
                return await self.replyInvalidCommand(event, "Please provide a channel")
            if parse_result[0].year == None and parse_result[0].month is not None:
                return await self.replyInvalidCommand(
                    event, "Please provide a year if you want to specify month"
                )
            return await handle_func(
                self,
                event,
                chan=chan,
                year=parse_result[0].year,
                month=parse_result[0].month,
                page=parse_result[0].page,
            )

        return await inner(self, event, raw_command)

    return wrapper


def recent_top_arg_handler(handle_func: Callable):
    async def wrapper(self: "AppService", event: Event, raw_command: str):
        @arg_hander(self.recent_top_args_parser)
        async def inner(
            self: "AppService",
            event: Event,
            parse_result: tuple[Namespace, list[str]],
        ):
            chan = None
            for i in [parse_result[0].channel2, parse_result[0].channel]:
                if i is not None:
                    if chan is not None:
                        return await self.replyInvalidCommand(
                            event, "Please provide only one channel"
                        )
                    chan = i
            return await handle_func(self, event, chan=chan, max=parse_result[0].max)

        return await inner(self, event, raw_command)

    return wrapper


class AppService:

    core_service: CoreService
    chans_args_parser: ArgumentParser
    top_args_parser: ArgumentParser
    recent_top_args_parser: ArgumentParser

    logger = logging.getLogger("teletop")

    def __init__(self, core_service_impl: CoreService):
        self.core_service = core_service_impl
        self._set_arg_parsers()

    def _set_arg_parsers(self):
        chans_ap = ArgumentParser(prog="command", exit_on_error=False)
        chans_ap.add_argument("channels2", nargs="*", help="list of channel username")
        chans_ap.add_argument(
            "-c", "--channels", nargs="*", default=[], help="list of channel username"
        )
        self.chans_args_parser = chans_ap

        chans_ap = ArgumentParser(prog="command", exit_on_error=False)
        chans_ap.add_argument("channel2", nargs="?", help="channel username")
        chans_ap.add_argument("-c", "--channel", nargs="?", help="channel username")
        chans_ap.add_argument("-y", "--year", nargs="?", type=int)
        chans_ap.add_argument("-m", "--month", nargs="?", type=int)
        chans_ap.add_argument("-p", "--page", nargs="?", type=int, default=1)
        self.top_args_parser = chans_ap

        chans_ap = ArgumentParser(prog="command", exit_on_error=False)
        chans_ap.add_argument("channel2", nargs="?", help="channel username")
        chans_ap.add_argument("-c", "--channel", nargs="?", help="channel username")
        chans_ap.add_argument(
            "-m", "--max", nargs="?", type=int, default=10, help="top n msgs"
        )
        self.recent_top_args_parser = chans_ap

    @no_arg_handler
    async def ping(self, event: Event):
        await event.reply(self.core_service.ping())

    @chans_arg_handler
    async def add_subscr(self, event: Event, chans: List) -> None:
        AppService.logger.debug(f"Start to add channels {chans}")
        try:
            results = await self.core_service.subscribe_channels(chans)
            reply_strs = []
            if len(results[0]) > 0:
                reply_strs.append(f"Success: {len(results[0])}\n{','.join(results[0])}")
            if len(results[1]) > 0:
                fail_reasons = "\n".join([f"{k}: {v}" for k, v in results[1]])
                reply_strs.append(f"Fail: {len(results[1])}\n{fail_reasons}")
            if len(results[2]) > 0:
                reply_strs.append(
                    f"Already subscribed: {len(results[2])}\n{','.join(results[2])}"
                )
            await event.reply("\n\n".join(reply_strs))
        except Exception as e:
            AppService.logger.error(f"Met error when adding channels: {e}")

    @chans_arg_handler
    async def rm_subscr(self, event: Event, chans: List) -> None:
        AppService.logger.debug(f"Start to remove channels {chans}")

    @chans_arg_handler
    async def check_subscr_status(self, event: Event, chans: List) -> None:
        AppService.logger.debug(f"Start to print status of {chans}")

    @no_arg_handler
    async def list_subscr(self, event: Event) -> None:
        AppService.logger.debug(f"Start to list subscriptions")

    @top_arg_handler
    async def list_top_msgs(
        self, event: Event, chan: str, year: int | None, month: int | None, page: int
    ) -> None:
        AppService.logger.debug(
            f"Start to list page {page} top msgs of channel '{chan}' at year {year} and month {month}"
        )

        try:
            msgs, total = await self.core_service.get_top_messages(
                chan, year, month, page
            )
        except Exception as e:
            await event.reply(f"Met error when getting top msgs: {e}")
            return

        button_data_prefix_parts = ["/top"]
        if year is not None:
            button_data_prefix_parts.append(f"-y {year}")
        if month is not None:
            button_data_prefix_parts.append(f"-m {month}")
        button_data_prefix = " ".join(button_data_prefix_parts)

        total_page = total // 10
        if total % 10 != 0:
            total_page += 1

        buttons = []
        if page > 1:
            buttons.append(Button.inline("prev", f"{button_data_prefix} -p {page-1}"))
        if page < total_page:
            buttons.append(Button.inline("next", f"{button_data_prefix} -p {page+1}"))

        chan_username = f"{chan.split('/')[-1]}"
        show_text_strs = [f"{chan_username}\n"]
        for msg in msgs:
            post_date = msg.post_datetime
            year_text = f"{post_date.year}"[-2:]
            date_text = f"{year_text}/{post_date.month:02}/{post_date.day:02}"
            show_text_strs.append(
                " ".join(
                    [
                        date_text,
                        f"[{msg.text[:30]}](https://t.me/{chan_username}/{msg.channel_msg_id})",
                        f"{msg.not_neg_reactions}",
                    ]
                )
            )
        show_text_strs.append(f"\npage {page}/{total_page}")
        show_text = "\n".join(show_text_strs)

        if isinstance(event, CallbackQuery.Event):
            await event.edit(show_text, buttons=buttons)
        else:
            await event.reply(show_text, buttons=buttons)

    @recent_top_arg_handler
    async def list_recent_tops(self, event: Event, chan: str, max: int):
        AppService.logger.debug(f"Start to list recent top msgs of channel '{chan}'")
        try:
            msgs = await self.core_service.get_recent_top_messages(chan, max)
        except Exception as e:
            await event.reply(f"Met error when getting recent top msgs: {e}")
            return
        
        chan_username = f"{chan.split('/')[-1]}"
        show_text_strs = [f"{chan_username}\n"]
        for msg in msgs:
            post_date = msg.post_datetime
            year_text = f"{post_date.year}"[-2:]
            date_text = f"{year_text}/{post_date.month:02}/{post_date.day:02}"
            show_text_strs.append(
                " ".join(
                    [
                        date_text,
                        f"[{msg.text[:30]}](https://t.me/{chan_username}/{msg.channel_msg_id})",
                        f"{msg.not_neg_reactions}",
                    ]
                )
            )
        show_text = "\n".join(show_text_strs)
        await event.reply(show_text)
        
        
    async def replyInvalidCommand(self, msg: Message, text: str = None) -> None:
        if text == None:
            text = "Invalid command"
        await msg.reply(text)

    async def start(self):
        await self.core_service.start()
