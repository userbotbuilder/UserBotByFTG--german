# -*- coding: future_fstrings -*-

#    Friendly Telegram (telegram userbot)
#    Copyright (C) 2018-2019 The Authors

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from .. import loader, utils

import logging

from telethon import functions, types
logger = logging.getLogger(__name__)


def register(cb):
    cb(AntiPMMod())


@loader.tds
class AntiPMMod(loader.Module):
    """Prevents people sending you unsolicited private messages"""
    strings = {"name": "Anti PM",
               "limit_cfg_doc": "Max number of PMs before user is blocked, or None",
               "who_to_block": "<b>Gib' an, wen du freigeben willst</b>",
               "blocked": ("<b>Du solltest es mit mir nicht anlegen, deshalb wurdest</b> <a href='tg://user?id={}'>DU</a> "
                           "<b>blockiert!</b>"),
               "who_to_unblock": "<b>Specify whom to unblock</b>",
               "unblocked": ("<b>Ah super! Diesmal vergebe ich ihm, ich habe PNs freigeschalten für </b> "
                             "<a href='tg://user?id={}'>diesen Nutzer</a>"),
               "who_to_allow": "<b>Wem soll ich es erlauben, dir zu schreiben?</b>",
               "allowed": "<b>Hi! Nun bin ich für</b> <a href='tg://user?id={}'>dich</a> <b>da!</b>",
               "who_to_report": "<b>Wenn soll ich melden?</b>",
               "reported": "<b>Ich habe dich nun zwecks spam gemeldet!</b>",
               "who_to_deny": "<b>Von wem soll ich die PNs ablehnen?</b>",
               "denied": ("<b>So</b> <a href='tg://user?id={}'>du</a> "
                          "<b>,Ich bin wieder offline. Ciao!</b>"),
               "notif_off": "<b>Benachrichtigungen für abgelehnte PNs sind nun deaktiviert.</b>",
               "notif_on": "<b>Benachrichtigungen für abgelehnte PNs sind nun aktiviert.</b>",
               "go_away": ("Hey Hey! Aktuell bin ich offline. "
                            "\n\nBitte gedulde dich ein wenig, ich <b>werde</b> "
                            "schnellstmöglich auf deine Nachricht antworten."),
               "triggered": ("Hey! Mir gefällt gar nicht, wie du mit mir umgehst! "
                             "Hast du mich zumindest freundlich begrüßt? Nein? Dann ciao."
                             "\n\nPS: Ich habe dich bereits wegen Spam gemeldet.")}

    def __init__(self):
        self.config = loader.ModuleConfig("PM_BLOCK_LIMIT", None, lambda: self.strings["limit_cfg_doc"])
        self._me = None
        self._ratelimit = []

    def config_complete(self):
        self.name = self.strings["name"]

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me(True)

    async def blockcmd(self, message):
        """Block this user to PM without being warned"""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_block"])
            return
        await message.client(functions.contacts.BlockRequest(user))
        await utils.answer(message, self.strings["blocked"].format(user))

    async def unblockcmd(self, message):
        """Unblock this user to PM"""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_unblock"])
            return
        await message.client(functions.contacts.UnblockRequest(user))
        await utils.answer(message, self.strings["unblocked"].format(user))

    async def allowcmd(self, message):
        """Allow this user to PM"""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_allow"])
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).union({user})))
        await utils.answer(message, self.strings["allowed"].format(user))

    async def reportcmd(self, message):
        """Report the user spam. Use only in PM"""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_report"])
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).difference({user})))
        if message.is_reply and isinstance(message.to_id, types.PeerChannel):
            # Report the message
            await message.client(functions.messages.ReportRequest(peer=message.chat_id,
                                                                  id=[message.reply_to_msg_id],
                                                                  reason=types.InputReportReasonSpam()))
        else:
            await message.client(functions.messages.ReportSpamRequest(peer=message.to_id))
        await utils.answer(message, self.strings["reported"])

    async def denycmd(self, message):
        """Deny this user to PM without being warned"""
        user = await utils.get_target(message)
        if not user:
            await utils.answer(message, self.strings["who_to_deny"])
            return
        self._db.set(__name__, "allow", list(set(self._db.get(__name__, "allow", [])).difference({user})))
        await utils.answer(message, self.strings["denied"].format(user))

    async def notifoffcmd(self, message):
        """Disable the notifications from denied PMs"""
        self._db.set(__name__, "notif", True)
        await utils.answer(message, self.strings["notif_off"])

    async def notifoncmd(self, message):
        """Enable the notifications from denied PMs"""
        self._db.set(__name__, "notif", False)
        await utils.answer(message, self.strings["notif_on"])

    async def watcher(self, message):
        if getattr(message.to_id, "user_id", None) == self._me.user_id:
            logger.debug("pm'd!")
            if message.from_id in self._ratelimit:
                self._ratelimit.remove(message.from_id)
                return
            else:
                self._ratelimit += [message.from_id]
            user = await utils.get_user(message)
            if user.is_self or user.bot or user.verified:
                logger.debug("User is self, bot or verified.")
                return
            if self.get_allowed(message.from_id):
                logger.debug("Authorised pm detected")
            else:
                await utils.answer(message, self.strings["go_away"])
                if isinstance(self.config["PM_BLOCK_LIMIT"], int):
                    limit = self._db.get(__name__, "limit", {})
                    if limit.get(message.from_id, 0) >= self.config["PM_BLOCK_LIMIT"]:
                        await utils.answer(message, self.strings["triggered"])
                        await message.client(functions.contacts.BlockRequest(message.from_id))
                        await message.client(functions.messages.ReportSpamRequest(peer=message.from_id))
                        del limit[message.from_id]
                        self._db.set(__name__, "limit", limit)
                    else:
                        self._db.set(__name__, "limit", {**limit, message.from_id: limit.get(message.from_id, 0) + 1})
                if self._db.get(__name__, "notif", False):
                    await message.client.send_read_acknowledge(message.chat_id)

    def get_allowed(self, id):
        return id in self._db.get(__name__, "allow", [])
