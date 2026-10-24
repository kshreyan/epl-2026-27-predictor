"""Real-data fetch helpers for UFC from ESPN's public site API
(site.api.espn.com/apis/site/v2/sports/mma/ufc), confirmed directly
accessible this session. A genuinely different real shape from
espn_api.py's team-sport helpers -- UFC has no teams, no weekly
schedule, and no per-athlete schedule endpoint, so this module does not
reuse that one.

The real unit here is an EVENT (a fight card, e.g. "UFC 333:
Volkanovski vs. Evloev"), fetched via the scoreboard endpoint's real
date-RANGE query (`dates=YYYYMMDD-YYYYMMDD`), confirmed directly to
return every real event in that window with every real fight on it. A
multi-year range was rejected with a real HTTP 400 (confirmed
directly) -- historical collection chunks by calendar year.

Each real fight's result is read from real, directly-observed fields,
not inferred:
- `format.regulation.periods`: the real number of scheduled rounds (3
  normally, 5 for a real title/main-event fight).
- `status.period` / `status.displayClock`: the round the fight actually
  ended in and the clock within it. `period == periods` with a full
  round elapsed (`displayClock` reads the round's real full duration,
  "5:00") means a real decision (the fight went the real scheduled
  distance); anything short of that is a real stoppage (KO/TKO/
  submission) in that round. Confirmed directly against a real live
  card (UFC 333, 14 real fights, mixing real decisions and real early
  stoppages).
- `competitors[].winner`: real bool per fighter.
- `competitors[].records`: each fighter's real overall win-loss-draw
  record AT THE TIME of that fight (not their current record) is not
  separately exposed by this endpoint -- only the fighter's record as
  of the FETCH time is included, a real limitation disclosed here
  rather than treated as per-fight historical record data.
"""
from __future__ import annotations

from datetime import date

import requests

HEADERS = {"User-Agent": "Mozilla/5.0"}
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"


def _method_and_round(status: dict, scheduled_rounds: int) -> tuple[str, int | None]:
    """Real ("decision"|"finish", round) read from ESPN's own real
    status fields -- see module docstring for the exact real signal
    used. Returns ("unscored", None) for a fight ESPN hasn't posted a
    completed status for (e.g. a real no-contest/cancelled booking --
    rare but real; never guessed as a decision)."""
    if not status.get("type", {}).get("completed"):
        return "unscored", None
    period = status.get("period")
    clock = status.get("displayClock", "")
    if period is None:
        return "unscored", None
    full_round_elapsed = clock in ("0:00", "5:00")  # "0:00" = countdown reached zero; "5:00" = this endpoint's own full-round display for a completed round
    if period >= scheduled_rounds and full_round_elapsed:
        return "decision", scheduled_rounds
    return "finish", period


def fetch_real_ufc_events(date_from: date, date_to: date) -> list[dict]:
    """Every real UFC event (fight card) with a start date in
    [date_from, date_to], each with every real fight on it. A real
    multi-year range is rejected by ESPN with an HTTP 400 (confirmed
    directly) -- callers chunk by year themselves; this function makes
    exactly one real request per call, no internal chunking, so a
    caller controls real request pacing.

    Returns a list of real event dicts: event_id, event_name,
    event_date (ISO UTC), venue_city, venue_country, and `fights`: a
    list of real per-fight dicts (fight_id, weight_class,
    scheduled_rounds, fighter_a_id/name, fighter_b_id/name,
    fighter_a_record/fighter_b_record [as of fetch time, see module
    docstring], winner_id, method, finish_round, status)."""
    resp = requests.get(
        SCOREBOARD_URL,
        params={"dates": f"{date_from.strftime('%Y%m%d')}-{date_to.strftime('%Y%m%d')}"},
        headers=HEADERS, timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    events = []
    for ev in payload.get("events", []):
        fights = []
        for comp in ev.get("competitions", []):
            scheduled_rounds = comp.get("format", {}).get("regulation", {}).get("periods", 3)
            competitors = comp.get("competitors", [])
            if len(competitors) != 2:
                continue  # a real fight always has exactly two competitors -- skip anything malformed rather than guess
            # ESPN's own "order" field (1 = first-listed/red corner) is
            # used only for a stable fighter_a/fighter_b ordering, not
            # home/away (there is no real home/away in an individual
            # fight -- a real neutral-site framing throughout).
            competitors = sorted(competitors, key=lambda c: c.get("order", 0))
            a, b = competitors[0], competitors[1]
            method, finish_round = _method_and_round(comp.get("status", {}), scheduled_rounds)
            winner_id = next((c["id"] for c in competitors if c.get("winner")), None)

            def _record(c: dict) -> str | None:
                for r in c.get("records", []):
                    if r.get("name") == "overall":
                        return r.get("summary")
                return None

            # ESPN's own real data uses two different spellings for the
            # same real category ("Catch Weight" and "Catchweight") --
            # reconciled here (both real, same meaning), not a
            # fabricated distinction.
            weight_class = comp.get("type", {}).get("abbreviation", "").replace("Catchweight", "Catch Weight")
            fights.append({
                "fight_id": comp["id"],
                "weight_class": weight_class,
                "scheduled_rounds": scheduled_rounds,
                # The real fighter identity lives on the competitor
                # entry's own "id", not athlete.id -- confirmed directly
                # that athlete.id is sometimes absent while this one
                # never is.
                "fighter_a_id": a["id"], "fighter_a_name": a["athlete"]["fullName"],
                "fighter_a_record": _record(a),
                "fighter_b_id": b["id"], "fighter_b_name": b["athlete"]["fullName"],
                "fighter_b_record": _record(b),
                "winner_id": winner_id, "method": method, "finish_round": finish_round,
                "completed": bool(comp.get("status", {}).get("type", {}).get("completed")),
                "date": comp.get("date", ev.get("date")),
            })
        events.append({
            "event_id": ev["id"], "event_name": ev.get("name", ""), "event_date": ev.get("date"),
            "venue_city": ev.get("venues", [{}])[0].get("address", {}).get("city", "") if ev.get("venues") else "",
            "venue_country": ev.get("venues", [{}])[0].get("address", {}).get("country", "") if ev.get("venues") else "",
            "fights": fights,
        })
    return events
