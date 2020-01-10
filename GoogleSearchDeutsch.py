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

import logging

from search_engine_parser import GoogleSearch

from .. import loader, utils

logger = logging.getLogger(__name__)


def register(cb):
    cb(GoogleSearchMod())


@loader.tds
class GoogleSearchMod(loader.Module):
    """Make a Google search, right in your chat!"""
    strings = {"name": "Google search",
               "no_term": "<b>Ich kann nicht nichts googlen</b>",
               "no_results": "<b>Ich habe nichts gefunden über:</b> <code>{}</code> <b>on Google</b>",
               "results": "<b>Das kam raus, wo ich das gesucht habe:</b> <code>{}</code>:\n\n",
               "result": "<a href='{}'>{}</a>\n\n<code>{}</code>\n"}

    def config_complete(self):
        self.name = self.strings["name"]

    async def googlecmd(self, message):
        """Shows Google search results."""
        text = utils.get_args_raw(message.message)
        if not text:
            text = (await message.get_reply_message()).message
        if not text:
            await utils.answer(message, self.strings["no_term"])
            return
        # TODO: add ability to specify page number.
        gsearch = GoogleSearch()
        gresults = await gsearch.async_search(text, 1)
        if not gresults:
            await utils.answer(message, self.strings["no_results"].format(text))
            return
        msg = ""
        results = zip(gresults["titles"], gresults["links"], gresults["descriptions"])
        for result in results:
            msg += self.strings["result"].format(utils.escape_html(result[0]), utils.escape_html(result[1]),
                                                 utils.escape_html(result[2]))
        await utils.answer(message, self.strings["results"].format(utils.escape_html(text)) + msg)