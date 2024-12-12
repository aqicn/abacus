import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError
from socket import timeout
import logging


class Response:
    text: str
    status_code: int

    def __init__(self, text, status_code):
        self.status_code = status_code
        self.text = text

    def json(self):
        try:
            output = json.loads(self.text)
        except json.JSONDecodeError:
            output = None
        return output


def Fetch(
    url: str,
    data: dict = None,
    params: dict = None,
    headers: dict = None,
    method: str = "GET",
):
    if not url.casefold().startswith("http"):
        raise urllib.error.URLError("Incorrect and possibly insecure protocol in url")
    method = method.upper()
    request_data = None
    headers = headers or {}
    data = data or {}
    params = params or {}
    headers = {"Accept": "application/json", **headers}

    if method == "GET":
        params = {**params, **data}
        data = None

    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True, safe="/")

    if data:
        request_data = json.dumps(data).encode()
        headers["Content-Type"] = "application/json; charset=UTF-8"

    httprequest = urllib.request.Request(
        url, data=request_data, headers=headers, method=method
    )

    print("fetch(%s): " % url, end="")
    sys.stdout.flush()

    response = None
    try:
        with urllib.request.urlopen(httprequest, timeout=10) as httpresponse:
            body = httpresponse.read().decode(
                httpresponse.headers.get_content_charset("utf-8")
            )
            response = Response(
                status_code=httpresponse.status,
                text=body,
            )

    except HTTPError as e:
        response = Response(status_code=0, text="http error: %s" % e)

    except URLError as e:
        if isinstance(e.reason, timeout):
            response = Response(status_code=0, text="http timeout")

        else:
            response = Response(status_code=0, text="generic error: %s" % e.reason)

    return response


# https://github.com/mpetazzoni/sseclient/blob/master/sseclient/__init__.py

_FIELD_SEPARATOR = ":"


class SSEClient(object):
    """Implementation of a SSE client.

    See http://www.w3.org/TR/2009/WD-eventsource-20091029/ for the
    specification.
    """

    def __init__(self, url, headers, char_enc="utf-8"):
        self._logger = logging.getLogger(self.__class__.__module__)
        httprequest = urllib.request.Request(url, headers=headers, method="GET")
        event_source = urllib.request.urlopen(httprequest, timeout=10)
        self._event_source = event_source
        self._char_enc = char_enc
        self._headers = headers

    def _read(self):
        """Read the incoming event source stream and yield event chunks.

        Unfortunately it is possible for some servers to decide to break an
        event into multiple HTTP chunks in the response. It is thus necessary
        to correctly stitch together consecutive response chunks and find the
        SSE delimiter (empty new line) to yield full, correct event chunks."""
        data = b""
        for chunk in self._event_source:
            for line in chunk.splitlines(True):
                data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield data
                    data = b""
        if data:
            yield data

    def events(self):
        for chunk in self._read():
            event = Event()
            # Split before decoding so splitlines() only uses \r and \n
            for line in chunk.splitlines():
                # Decode the line.
                line = line.decode(self._char_enc)

                # Lines starting with a separator are comments and are to be
                # ignored.
                if not line.strip() or line.startswith(_FIELD_SEPARATOR):
                    continue

                data = line.split(_FIELD_SEPARATOR, 1)
                field = data[0]

                # Ignore unknown fields.
                if field not in event.__dict__:
                    self._logger.debug(
                        "Saw invalid field %s while parsing " "Server Side Event", field
                    )
                    continue

                if len(data) > 1:
                    # From the spec:
                    # "If value starts with a single U+0020 SPACE character,
                    # remove it from value."
                    if data[1].startswith(" "):
                        value = data[1][1:]
                    else:
                        value = data[1]
                else:
                    # If no value is present after the separator,
                    # assume an empty value.
                    value = ""

                # The data field may come over multiple lines and their values
                # are concatenated with each other.
                if field == "data":
                    event.__dict__[field] += value + "\n"
                else:
                    event.__dict__[field] = value

            # Events with no data are not dispatched.
            if not event.data:
                continue

            # If the data field ends with a newline, remove it.
            if event.data.endswith("\n"):
                event.data = event.data[0:-1]

            # Empty event names default to 'message'
            event.event = event.event or "message"

            # Dispatch the event
            self._logger.debug("Dispatching %s...", event)
            yield event

    def close(self):
        """Manually close the event source stream."""
        self._event_source.close()


class Event(object):
    """Representation of an event from the event stream."""

    def __init__(self, id=None, event="message", data="", retry=None):
        self.id = id
        self.event = event
        self.data = data
        self.retry = retry

    def __str__(self):
        s = "{0} event".format(self.event)
        if self.id:
            s += " #{0}".format(self.id)
        if self.data:
            s += ", {0} byte{1}".format(len(self.data), "s" if len(self.data) else "")
        else:
            s += ", no data"
        if self.retry:
            s += ", retry in {0}ms".format(self.retry)
        return s
