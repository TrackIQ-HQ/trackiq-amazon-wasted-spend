#!/usr/bin/env python3
"""Build the Amazon bulk-operations workbook from a sweep result.

An accelerant, not a dependency: the column contract is written out in
assets/method.md, so the workbook can be produced by hand if this will not
run (no openpyxl, no filesystem).

    python build_workbook.py            # self-check
    python build_workbook.py sweep.json out.xlsx

Input JSON:
  {"totals": {"be": 2.0, "days": 30, "union": 144, "union_spend": 46319.0,
              "excess": 17072.0},
   "zero":  [{"kw","mt","spend","clicks","bid","tid","agid","cid","ag"}],
   "bleed": [{"kw","mt","spend","sales","orders","roas","bid","over",
              "tid","agid","cid","ag"}],
   "dups":  [{"kw","mt","winner_roas","winner_ag","amt",
              "losers":[{"ag","spend","roas","tid","agid","cid"}]}],
   "terms": [{"q","spend","clicks"}]}
"""
from __future__ import annotations

import json
import sys

BULK_COLS = ["Product", "Entity", "Operation", "Campaign ID", "Ad Group ID", "Keyword ID",
             "Keyword Text", "Match Type", "State", "Bid", "TrackIQ reason"]


def bulk_rows(d: dict) -> list[list]:
    """One row per proposed change. Pause rows set State and leave Bid blank;
    bid rows set Bid and leave State blank. Never both."""
    be = d["totals"]["be"]
    out, seen = [], set()

    def row(cid, agid, tid, kw, mt, state, bid, reason):
        return ["Sponsored Products", "Keyword", "update", cid, agid, tid,
                kw, mt, state, bid, reason]

    for k in d.get("zero", []):
        if None in (k.get("cid"), k.get("agid"), k.get("tid")):
            continue                      # never ship a row with a missing ID
        out.append(row(k["cid"], k["agid"], k["tid"], k["kw"], k["mt"], "paused", None,
                       f"${k['spend']:,.0f} spent, {k['clicks']} clicks, 0 orders"))
        seen.add(k["tid"])

    for g in d.get("dups", []):
        for l in g.get("losers", []):
            if None in (l.get("cid"), l.get("agid"), l.get("tid")) or l["tid"] in seen:
                continue
            out.append(row(l["cid"], l["agid"], l["tid"], g["kw"], g["mt"], "paused", None,
                           f"duplicate: {g['winner_roas']}x in {g['winner_ag']}, "
                           f"{l['roas']}x here"))
            seen.add(l["tid"])

    for k in d.get("bleed", []):
        if k["tid"] in seen or not k.get("bid"):
            continue
        if None in (k.get("cid"), k.get("agid")):
            continue
        factor = max(0.5, k["roas"] / be)
        out.append(row(k["cid"], k["agid"], k["tid"], k["kw"], k["mt"], None,
                       round(k["bid"] * factor, 2),
                       f"{k['roas']}x vs {be}x break-even, ${k['over']:,.0f} over"))
        seen.add(k["tid"])
    return out


def write(d: dict, path: str) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    SAGE, PALE, PROB = "FF17533F", "FFF1F5EF", "FFFFF3F1"
    hf = Font(name="Inter", bold=True, color="FFFDFBFA", size=10)
    bf = Font(name="Inter", size=10)
    wb = Workbook(); wb.remove(wb.active)

    def sheet(title, cols, rows, widths, fill=None):
        ws = wb.create_sheet(title)
        ws.append(cols)
        for c in range(1, len(cols) + 1):
            cell = ws.cell(row=1, column=c)
            cell.font, cell.fill = hf, PatternFill("solid", fgColor=SAGE)
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 28
        for i, r in enumerate(rows, start=2):
            ws.append(r)
            for c in range(1, len(cols) + 1):
                cell = ws.cell(row=i, column=c)
                cell.font = bf
                if fill and fill(r):
                    cell.fill = PatternFill("solid", fgColor=fill(r))
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    t, be = d["totals"], d["totals"]["be"]
    ws = wb.create_sheet("Read me")
    for r in [["Wasted-spend sweep", ""], ["", ""],
              ["Window", f"{t['days']} days, Sponsored Products keywords"],
              ["Break-even ROAS used", f"{be}x - AN ASSUMPTION unless set from product margin"],
              ["Keywords flagged", t["union"]],
              ["Their spend", t["union_spend"]],
              ["Spend above break-even value", t["excess"]],
              ["", ""], ["Before you upload", ""],
              ["1", "Sponsored Products only, Operation=update."],
              ["2", "Pause rows set State=paused. Bid rows set Bid and leave State blank."],
              ["3", "Nothing is applied automatically. Review, then upload in Campaign Manager."],
              ["4", "Bid changes scale the current bid by the shortfall to break-even,"],
              ["", "floored at a 50% cut - a starting point, not an optimum."],
              ["5", "Negative candidates are NOT uploadable: the search-term report does not"],
              ["", "say which campaign a term spent in. Choose the placement yourself."],
              ["6", "Check whether the source pulls hit their row limit; if so these are a floor."]]:
        ws.append(r)
    ws.column_dimensions["A"].width = 30; ws.column_dimensions["B"].width = 95
    ws["A1"].font = Font(name="Inter", bold=True, size=14, color=SAGE[2:])

    sheet("Bulk upload", BULK_COLS, bulk_rows(d),
          [18, 10, 10, 16, 16, 16, 34, 10, 9, 8, 52],
          fill=lambda r: PROB if r[8] == "paused" else None)
    sheet("Below break-even",
          ["Keyword", "Match", "Ad group", "Spend", "Sales", "ROAS", "Orders", "Bid",
           "Spend above break-even value"],
          [[k["kw"], k["mt"], k.get("ag"), k["spend"], k["sales"], k["roas"], k["orders"],
            k["bid"], k["over"]] for k in d.get("bleed", [])],
          [34, 9, 34, 11, 11, 8, 8, 8, 26])
    dup = []
    for g in d.get("dups", []):
        dup.append([g["kw"], g["mt"], "KEEP", g["winner_ag"], None, g["winner_roas"], None])
        for l in g["losers"]:
            dup.append([g["kw"], g["mt"], "pause", l["ag"], l["spend"], l["roas"], l["spend"]])
    sheet("Duplicates", ["Keyword", "Match", "Action", "Ad group", "Spend", "ROAS",
                         "Spend to redirect"], dup, [30, 9, 9, 34, 11, 8, 18],
          fill=lambda r: PALE if r[2] == "KEEP" else PROB)
    sheet("Negative candidates", ["Search term", "Spend", "Clicks", "Orders", "Note"],
          [[x["q"], x["spend"], x["clicks"], 0,
            "placement not in the data - choose the campaign before uploading"]
           for x in d.get("terms", [])], [46, 11, 9, 9, 62])
    wb.save(path)


def _selfcheck():
    d = {"totals": {"be": 2.0, "days": 30, "union": 3, "union_spend": 900.0, "excess": 400.0},
         "zero": [{"kw": "patio lights", "mt": "broad", "spend": 140.0, "clicks": 27, "bid": 5.5,
                   "tid": 1, "agid": 10, "cid": 100, "ag": "AG A"},
                  {"kw": "no ids", "mt": "broad", "spend": 90.0, "clicks": 9, "bid": 1.0,
                   "tid": 9, "agid": None, "cid": None, "ag": None}],
         "bleed": [{"kw": "outdoor lights", "mt": "broad", "spend": 3461.0, "sales": 1622.0,
                    "orders": 29, "roas": 0.47, "bid": 1.51, "over": 2650.0,
                    "tid": 2, "agid": 11, "cid": 101, "ag": "AG B"},
                   {"kw": "dup kw", "mt": "exact", "spend": 500.0, "sales": 100.0, "orders": 2,
                    "roas": 0.2, "bid": 2.0, "over": 450.0,
                    "tid": 3, "agid": 12, "cid": 102, "ag": "AG C"}],
         "dups": [{"kw": "dup kw", "mt": "exact", "winner_roas": 3.4, "winner_ag": "AG W",
                   "amt": 500.0,
                   "losers": [{"ag": "AG C", "spend": 500.0, "roas": 0.2,
                               "tid": 3, "agid": 12, "cid": 102}]}],
         "terms": [{"q": "solar garden lights", "spend": 83.0, "clicks": 13}]}
    rows = bulk_rows(d)

    assert all(r[3] is not None and r[4] is not None and r[5] is not None for r in rows), \
        "no row may ship with a missing ID"
    assert not any(r[5] == 9 for r in rows), "row with null ids must be dropped"
    ids = [r[5] for r in rows]
    assert len(ids) == len(set(ids)), "a keyword must not appear twice"
    assert sum(1 for r in rows if r[5] == 3) == 1, "dup pause must win over a bid change"
    assert [r for r in rows if r[5] == 3][0][8] == "paused"
    for r in rows:
        assert (r[8] == "paused") != (r[9] is not None), \
            "each row sets State or Bid, never both, never neither"
    bid_row = [r for r in rows if r[5] == 2][0]
    assert bid_row[9] == round(1.51 * max(0.5, 0.47 / 2.0), 2), "bid scaling"
    assert all(r[10] for r in rows), "every row needs a readable reason"
    assert rows[0][0] == "Sponsored Products" and rows[0][1] == "Keyword" and rows[0][2] == "update"
    print(f"build_workbook self-check: 8/8 passed ({len(rows)} rows from 4 candidates)")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        write(json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2])
        print("wrote", sys.argv[2])
    else:
        _selfcheck()
