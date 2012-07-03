# -*- coding: utf-8  -*-
#
# Copyright (C) 2009-2012 by Ben Kurtovic <ben.kurtovic@verizon.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import re

__all__ = ["Data"]

class Data(object):
    """Store data from an individual line received on IRC."""

    def __init__(self, bot, my_nick, line, msgtype):
        self._bot = bot
        self._my_nick = my_nick
        self._line = line

        self._is_private = self._is_command = False
        self._msg = self._command = self._trigger = None
        self._args = []
        self._kwargs = {}

        self._parse(msgtype)

    def _parse(self, msgtype):
        """Parse a line from IRC into its components as instance attributes."""
        sender = re.findall(":(.*?)!(.*?)@(.*?)\Z", line[0])[0]
        self._nick, self._ident, self._host = sender
        self._chan = self.line[2]

        if msgtype == "PRIVMSG":
            if self.chan == self.my_nick:
                # This is a privmsg to us, so set 'chan' as the nick of the
                # sender instead of the 'channel', which is ourselves:
                self._chan = self._nick
                self._is_private = True
            self._msg = " ".join(line[3:])[1:]
            self._parse_args()
            self._parse_kwargs()

    def _parse_args(self):
        """Parse command arguments from the message.

        self.msg is converted into the string self.command and the argument
        list self.args if the message starts with a "trigger" ("!", ".", or the
        bot's name); self.is_command will be set to True, and self.trigger will
        store the trigger string. Otherwise, is_command will be set to False.
        """
        self._args = self.msg.strip().split()[1:]

        try:
            self._command = args[0].lower()
        except IndexError:
            return

        if self.command.startswith("!") or self.command.startswith("."):
            # e.g. "!command arg1 arg2"
            self._is_command = True
            self._trigger = self.command[0]
            self._command = self.command[1:]  # Strip the "!" or "."
        elif self.command.startswith(self.my_nick):
            # e.g. "EarwigBot, command arg1 arg2"
            self._is_command = True
            self._trigger = self.my_nick
            try:
                self._command = self.args.pop(0).lower()
            except IndexError:
                self._command = ""

    def _parse_kwargs(self):
        """Parse keyword arguments embedded in self.args.

        Parse a command given as "!command key1=value1 key2=value2..." into a
        dict, self.kwargs, like {'key1': 'value2', 'key2': 'value2'...}.
        """
        for arg in self.args[2:]:
            try:
                key, value = re.findall("^(.*?)\=(.*?)$", arg)[0]
            except IndexError:
                pass
            if key and value:
                self.kwargs[key] = value

    @property
    def my_nick(self):
        """Our nickname, *not* the nickname of the sender."""
        return self._my_nick

    @property
    def line(self):
        """The full message received on IRC, including escape characters."""
        return self._line

    @property
    def chan(self):
        """Channel the message was sent from.

        This will be equal to :py:attr:`nick` if the message is a private
        message.
        """
        return self._chan

    @property
    def nick(self):
        """Nickname of the sender."""
        return self._nick

    @property
    def ident(self):
        """`Ident <http://en.wikipedia.org/wiki/Ident>`_ of the sender."""
        return self._ident

    @property
    def host(self):
        """Hostname of the sender."""
        return self._host

    @property
    def msg(self):
        """Text of the sent message, if it is a message, else ``None``."""
        return self._msg

    @property
    def is_private(self):
        """``True`` if this message was sent to us *only*, else ``False``."""
        return self._is_private

    @property
    def is_command(self):
        """Boolean telling whether or not this message is a bot command.

        A message is considered a command if and only if it begins with the
        character ``"!"``, ``"."``, or the bot's name followed by optional
        punctuation and a space (so ``EarwigBot: do something``, ``EarwigBot,
        do something``, and ``EarwigBot do something`` are all valid).
        """
        return self._is_command

    @property
    def command(self):
        """If the message is a command, this is the name of the command used.

        See :py:attr:`is_command <self.is_command>` for when a message is
        considered a command. If it's not a command, this will be set to
        ``None``.
        """
        return self._command

    @property
    def trigger(self):
        """If this message is a command, this is what triggered it.

        It can be either "!" (``"!help"``), "." (``".help"``), or the bot's
        name (``"EarwigBot: help"``). Otherwise, it will be ``None``."""
        return self._trigger

    @property
    def args(self):
        """List of all arguments given to this command.

        For example, the message ``"!command arg1 arg2 arg3=val3"`` will
        produce the args ``["arg1", "arg2", "arg3=val3"]``. This is empty if
        the message was not a command or if it doesn't have arguments.
        """
        return self._args

    @property
    def kwargs(self):
        """Dictionary of keyword arguments given to this command.

        For example, the message ``"!command arg1=val1 arg2=val2"`` will
        produce the kwargs ``{"arg1": "val1", "arg2": "val2"}``. This is empty
        if the message was not a command or if it doesn't have keyword
        arguments.
        """
        return self._kwargs
