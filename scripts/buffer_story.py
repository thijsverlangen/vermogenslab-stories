"""Nieuws-story inplannen in Buffer (Instagram en Facebook) via de GraphQL API.

De API-key komt uit de omgevingsvariabele BUFFER_KEY (staat in de routine, nooit in deze repository).
De afbeelding moet een publieke URL zijn: de raw-URL van de slide in deze repository.

Gebruik:
    from buffer_story import plan_story, check
    plan_story("instagram", url, "2026-09-25T10:00:00.000Z")   # -> (True, post_id) of (False, fout)
"""
import json, os, time, urllib.request

ORG = "67fe2a2828e7d3f7989a61d9"
CH = {"instagram": "67fe2b382799bb0a23236428", "facebook": "6801edfa2799bb0a234fe466"}
MUT = """mutation CreatePost($input: CreatePostInput!) { createPost(input: $input) { __typename
  ... on PostActionSuccess { post { id dueAt status } } ... on InvalidInputError { message }
  ... on UnexpectedError { message } ... on RestProxyError { message } } }"""


def gql(query, variables=None):
    key = os.environ.get("BUFFER_KEY", "").strip()
    if not key:
        raise RuntimeError("BUFFER_KEY ontbreekt")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    for _ in range(4):
        req = urllib.request.Request("https://api.buffer.com/", data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.load(r)
        if d.get("errors") and any("Too many" in str(e) for e in d["errors"]):
            time.sleep(60); continue
        return d
    return d


def plan_story(kanaal, url, due, draft=False):
    inp = {"channelId": CH[kanaal], "text": "", "assets": [{"image": {"url": url}}],
           "mode": "customScheduled", "needsApproval": False, "schedulingType": "automatic", "dueAt": due}
    if draft:
        inp["saveToDraft"] = True
    if kanaal == "instagram":
        inp["metadata"] = {"instagram": {"type": "story", "shouldShareToFeed": False}}
    else:
        inp["metadata"] = {"facebook": {"type": "story"}}
    res = gql(MUT, {"input": inp})
    cp = (res.get("data") or {}).get("createPost") or {}
    if cp.get("__typename") == "PostActionSuccess":
        return True, cp["post"]["id"]
    return False, json.dumps(res)[:300]


def check():
    d = gql('query { posts(input: {organizationId: "' + ORG + '", filter: {status: [scheduled]}}, first: 1) { edges { node { id } } } }')
    if d.get("errors"):
        raise RuntimeError(str(d["errors"][0].get("message")))
    return "ok"
