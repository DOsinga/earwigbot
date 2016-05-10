# -*- coding: utf-8  -*-
#
# Copyright (C) 2009-2016 Ben Kurtovic <ben.kurtovic@gmail.com>
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

from gzip import GzipFile
from json import loads
from re import sub as re_sub
from socket import error
from StringIO import StringIO
from urllib import quote, urlencode
from urllib2 import URLError

from earwigbot import importer
from earwigbot.exceptions import SearchQueryError

etree = importer.new("lxml.etree")
oauth = importer.new("oauth2")

__all__ = ["BingSearchEngine", "YahooBOSSSearchEngine", "YandexSearchEngine",
           "SEARCH_ENGINES"]

class _BaseSearchEngine(object):
    """Base class for a simple search engine interface."""
    name = "Base"

    def __init__(self, cred, opener):
        """Store credentials (*cred*) and *opener* for searching later on."""
        self.cred = cred
        self.opener = opener
        self.count = 5

    def __repr__(self):
        """Return the canonical string representation of the search engine."""
        return "{0}()".format(self.__class__.__name__)

    def __str__(self):
        """Return a nice string representation of the search engine."""
        return "<{0}>".format(self.__class__.__name__)

    @staticmethod
    def requirements():
        """Return a list of packages required by this search engine."""
        return []

    def search(self, query):
        """Use this engine to search for *query*.

        Not implemented in this base class; overridden in subclasses.
        """
        raise NotImplementedError()


class BingSearchEngine(_BaseSearchEngine):
    """A search engine interface with Bing Search (via Azure Marketplace)."""
    name = "Bing"

    def __init__(self, cred, opener):
        super(BingSearchEngine, self).__init__(cred, opener)

        key = self.cred["key"]
        auth = (key + ":" + key).encode("base64").replace("\n", "")
        self.opener.addheaders.append(("Authorization", "Basic " + auth))

    def search(self, query):
        """Do a Bing web search for *query*.

        Returns a list of URLs ranked by relevance (as determined by Bing).
        Raises :py:exc:`~earwigbot.exceptions.SearchQueryError` on errors.
        """
        service = "SearchWeb" if self.cred["type"] == "searchweb" else "Search"
        url = "https://api.datamarket.azure.com/Bing/{0}/Web?".format(service)
        params = {
            "$format": "json",
            "$top": str(self.count),
            "Query": "'\"" + query.replace('"', "").encode("utf8") + "\"'",
            "Market": "'en-US'",
            "Adult": "'Off'",
            "Options": "'DisableLocationDetection'",
            "WebSearchOptions": "'DisableHostCollapsing+DisableQueryAlterations'"
        }

        try:
            response = self.opener.open(url + urlencode(params))
            result = response.read()
        except (URLError, error) as exc:
            raise SearchQueryError("Bing Error: " + str(exc))

        if response.headers.get("Content-Encoding") == "gzip":
            stream = StringIO(result)
            gzipper = GzipFile(fileobj=stream)
            result = gzipper.read()

        if response.getcode() != 200:
            err = "Bing Error: got response code '{0}':\n{1}'"
            raise SearchQueryError(err.format(response.getcode(), result))
        try:
            res = loads(result)
        except ValueError:
            err = "Bing Error: JSON could not be decoded"
            raise SearchQueryError(err)

        try:
            results = res["d"]["results"]
        except KeyError:
            return []
        return [result["Url"] for result in results]


class YahooBOSSSearchEngine(_BaseSearchEngine):
    """A search engine interface with Yahoo! BOSS."""
    name = "Yahoo! BOSS"

    @staticmethod
    def _build_url(base, params):
        """Works like urllib.urlencode(), but uses %20 for spaces over +."""
        enc = lambda s: quote(s.encode("utf8"), safe="")
        args = ["=".join((enc(k), enc(v))) for k, v in params.iteritems()]
        return base + "?" + "&".join(args)

    @staticmethod
    def requirements():
        return ["oauth2"]

    def search(self, query):
        """Do a Yahoo! BOSS web search for *query*.

        Returns a list of URLs ranked by relevance (as determined by Yahoo).
        Raises :py:exc:`~earwigbot.exceptions.SearchQueryError` on errors.
        """
        key, secret = self.cred["key"], self.cred["secret"]
        consumer = oauth.Consumer(key=key, secret=secret)

        url = "http://yboss.yahooapis.com/ysearch/web"
        params = {
            "oauth_version": oauth.OAUTH_VERSION,
            "oauth_nonce": oauth.generate_nonce(),
            "oauth_timestamp": oauth.Request.make_timestamp(),
            "oauth_consumer_key": consumer.key,
            "q": '"' + query.encode("utf8") + '"',
            "count": str(self.count),
            "type": "html,text,pdf",
            "format": "json",
        }

        req = oauth.Request(method="GET", url=url, parameters=params)
        req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), consumer, None)
        try:
            response = self.opener.open(self._build_url(url, req))
            result = response.read()
        except (URLError, error) as exc:
            raise SearchQueryError("Yahoo! BOSS Error: " + str(exc))

        if response.headers.get("Content-Encoding") == "gzip":
            stream = StringIO(result)
            gzipper = GzipFile(fileobj=stream)
            result = gzipper.read()

        if response.getcode() != 200:
            err = "Yahoo! BOSS Error: got response code '{0}':\n{1}'"
            raise SearchQueryError(err.format(response.getcode(), result))
        try:
            res = loads(result)
        except ValueError:
            err = "Yahoo! BOSS Error: JSON could not be decoded"
            raise SearchQueryError(err)

        try:
            results = res["bossresponse"]["web"]["results"]
        except KeyError:
            return []
        return [result["url"] for result in results]


class YandexSearchEngine(_BaseSearchEngine):
    """A search engine interface with Yandex Search."""
    name = "Yandex"

    @staticmethod
    def requirements():
        return ["lxml"]

    def search(self, query):
        """Do a Yandex web search for *query*.

        Returns a list of URLs ranked by relevance (as determined by Yandex).
        Raises :py:exc:`~earwigbot.exceptions.SearchQueryError` on errors.
        """
        url = "https://yandex.com/search/xml"
        query = re_sub(r"[^a-zA-Z0-9]", "", query).encode("utf8")
        params = {
            "user": self.cred["user"],
            "key": self.cred["key"],
            "query": '"' + query + '"',
            "l10n": "en",
            "filter": "none",
            "maxpassages": "1",
            "groupby": "mode=flat.groups-on-page={0}".format(self.count)
        }

        try:
            response = self.opener.open(url, urlencode(params))
            result = response.read()
        except (URLError, error) as exc:
            raise SearchQueryError("Yandex Error: " + str(exc))

        try:
            data = etree.fromstring(result)
            return [elem.text for elem in data.xpath(".//url")]
        except etree.Error as exc:
            raise SearchQueryError("Yandex XML parse error: " + str(exc))


SEARCH_ENGINES = {
    "Bing": BingSearchEngine,
    "Yahoo! BOSS": YahooBOSSSearchEngine,
    "Yandex": YandexSearchEngine
}
