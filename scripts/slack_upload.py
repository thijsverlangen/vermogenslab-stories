"""Berichten en afbeeldingen in Slack plaatsen via de Slack-app "Vermogenslab Stories".

Het bot-token komt uit de omgevingsvariabele SLACK_TOKEN (staat in de routine, nooit in deze repository).

Gebruik:
    from slack_upload import bericht, upload_afbeelding
    ts = bericht("C0C1MU54N81", "tekst")
    ts = upload_afbeelding("C0C1MU54N81", "/pad/slide.png", "Optie 1: kop")
"""
import json, os, time, urllib.request, urllib.parse


def _token():
    t = os.environ.get("SLACK_TOKEN", "").strip()
    if not t:
        raise RuntimeError("SLACK_TOKEN ontbreekt")
    return t


def _api(methode, data=None, json_body=None):
    headers = {"Authorization": "Bearer " + _token()}
    if json_body is not None:
        body = json.dumps(json_body).encode()
        headers["Content-Type"] = "application/json; charset=utf-8"
    else:
        body = urllib.parse.urlencode(data or {}).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request("https://slack.com/api/" + methode, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if not d.get("ok"):
        raise RuntimeError(f"Slack {methode} mislukt: {d.get('error', d)}")
    return d


def bericht(kanaal, tekst, thread_ts=None):
    body = {"channel": kanaal, "text": tekst, "unfurl_links": False, "unfurl_media": False}
    if thread_ts:
        body["thread_ts"] = thread_ts
    return _api("chat.postMessage", json_body=body)["ts"]


def upload_afbeelding(kanaal, pad, tekst="", thread_ts=None, wacht=20):
    """Uploadt een afbeelding naar het kanaal en geeft de ts van het bericht terug."""
    naam = os.path.basename(pad)
    inhoud = open(pad, "rb").read()
    r = _api("files.getUploadURLExternal", data={"filename": naam, "length": len(inhoud)})
    req = urllib.request.Request(r["upload_url"], data=inhoud, headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=120) as up:
        if up.status >= 300:
            raise RuntimeError(f"upload naar Slack mislukt (HTTP {up.status})")
    body = {"files": [{"id": r["file_id"], "title": naam}], "channel_id": kanaal}
    if tekst:
        body["initial_comment"] = tekst
    if thread_ts:
        body["thread_ts"] = thread_ts
    _api("files.completeUploadExternal", json_body=body)
    for _ in range(wacht):
        info = _api("files.info", data={"file": r["file_id"]})
        shares = info.get("file", {}).get("shares", {})
        for soort in ("private", "public"):
            if kanaal in shares.get(soort, {}):
                return shares[soort][kanaal][0]["ts"]
        time.sleep(1)
    raise RuntimeError("afbeelding geplaatst, maar de ts is niet gevonden")


def check():
    return _api("auth.test", json_body={}).get("user")
