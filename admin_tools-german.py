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

from telethon.tl.types import ChatAdminRights, ChatBannedRights, PeerUser, PeerChannel
from telethon.errors import BadRequestError
from telethon.tl.functions.channels import EditAdminRequest, EditBannedRequest

logger = logging.getLogger(__name__)


def register(cb):
    cb(BanMod())


@loader.tds
class BanMod(loader.Module):
    """Group administration tasks"""
    strings = {"name": "Administration",
               "ban_not_supergroup": "<b>Ich kann niemanden bannen, solange er in keiner Supergruppe ist!</b>",
               "unban_not_supergroup": "<b>Ich kann niemanden entbannen, solange er in keiner Supergruppe gebannt wurde!</b>",
               "kick_not_group": "<b>Ich kann niemanden kicken, der nicht in einer Gruppe ist!</b>",
               "ban_none": "<b>Ich kann niemnden bannen, kann ich?</b>",
               "unban_none": "<b>Es gibt niemanden zum entbannen.</b>",
               "kick_none": "<b>Das Mitglied muss sich in der Gruppe befinden, damit ich es kicken kann!</b>",
               "promote_none": "<b>Ich kann niemanden hochstufen, kann ich das denn?</b>",
               "demote_none": "<b>Ich kann keinen herabstufen, kann ich das denn?</b>",
               "who": "<b>Wer zur Hölle ist das?</b>",
               "not_admin": "<b>Bin ich admin hier?</b>",
               "banned": "<b>Ich habe</b> <code>{}</code> <b>aus dieser Gruppe gebannt!</b>",
               "unbanned": "<b>Der Nutzer</b> <code>{}</code> <b>kann der Gruppe wieder beitreten!</b>",
               "kicked": "<b>Ich habe</b> <code>{}</code> <b>aus dieser Gruppe rausgeschmissen!</b>",
               "promoted": "<code>{}</code> <b>Zesitzt jetzt Adminrechte!</b>",
               "demoted": "<code>{}</code> <b>Wurde als admin entlassen!</b>"}

    def __init__(self):
        self.name = self.strings["name"]

    async def bancmd(self, message):
        """Ban the user from the group"""
        if not isinstance(message.to_id, PeerChannel):
            return await utils.answer(message, self.strings["not_supergroup"])
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings["ban_none"])
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings["who"])
        logger.debug(user)
        try:
            await self.client(EditBannedRequest(message.chat_id, user.id,
                                                ChatBannedRights(until_date=None, view_messages=True)))
        except BadRequestError:
            await utils.answer(message, self.strings["not_admin"])
        else:
            await self.allmodules.log("ban", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings["banned"].format(utils.escape_html(ascii(user.first_name))))

    async def unbancmd(self, message):
        """Lift the ban off the user."""
        if not isinstance(message.to_id, PeerChannel):
            return await utils.answer(message, self.strings["unban_not_supergroup"])
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings["unban_none"])
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings["who"])
        logger.debug(user)
        try:
            await self.client(EditBannedRequest(message.chat_id, user.id,
                              ChatBannedRights(until_date=None, view_messages=False)))
        except BadRequestError:
            await utils.answer(message, self.strings["not_admin"])
        else:
            await self.allmodules.log("unban", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings["unbanned"].format(utils.escape_html(ascii(user.first_name))))

    async def kickcmd(self, message):
        """Kick the user out of the group"""
        if isinstance(message.to_id, PeerUser):
            return await utils.answer(message, self.strings["kick_not_group"])
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings["kick_none"])
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings["who"])
        logger.debug(user)
        try:
            await self.client.kick_participant(message.chat_id, user.id)
        except BadRequestError:
            await utils.answer(message, self.strings["not_admin"])
        else:
            await self.allmodules.log("kick", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings["kicked"].format(utils.escape_html(ascii(user.first_name))))

    async def promotecmd(self, message):
        """Provides admin rights to the specified user."""
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings["promote_none"])
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings["who"])
        logger.debug(user)
        try:
            await self.client(EditAdminRequest(message.chat_id, user.id,
                              ChatAdminRights(post_messages=None,
                                              add_admins=None,
                                              invite_users=None,
                                              change_info=None,
                                              ban_users=None,
                                              delete_messages=True,
                                              pin_messages=True,
                                              edit_messages=None), "Admin"))
        except BadRequestError:
            await utils.answer(message, self.strings["not_admin"])
        else:
            await self.allmodules.log("promote", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings["promoted"].format(utils.escape_html(ascii(user.first_name))))

    async def demotecmd(self, message):
        """Removes admin rights of the specified group admin."""
        if message.is_reply:
            user = await utils.get_user(await message.get_reply_message())
        else:
            args = utils.get_args(message)
            if len(args) == 0:
                return await utils.answer(message, self.strings["demote_none"])
            user = await self.client.get_entity(args[0])
        if not user:
            return await utils.answer(message, self.strings["who"])
        logger.debug(user)
        try:
            await self.client(EditAdminRequest(message.chat_id, user.id,
                              ChatAdminRights(post_messages=None,
                                              add_admins=None,
                                              invite_users=None,
                                              change_info=None,
                                              ban_users=None,
                                              delete_messages=None,
                                              pin_messages=None,
                                              edit_messages=None), "Admin"))
        except BadRequestError:
            await utils.answer(message, self.strings["not_admin"])
        else:
            await self.allmodules.log("demote", group=message.chat_id, affected_uids=[user.id])
            await utils.answer(message, self.strings["demoted"].format(utils.escape_html(ascii(user.first_name))))

    async def client_ready(self, client, db):
        self.client = client