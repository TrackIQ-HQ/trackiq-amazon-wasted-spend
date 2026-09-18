---
name: trackiq-amazon-wasted-spend
description: Finds Amazon advertising spend that is not paying for itself — keywords that spent and sold nothing, keywords bidding above what they return, the same keyword duplicated across ad groups bidding against itself, and search terms worth negating — then produces an Amazon bulk-operations workbook with the campaign, ad group and keyword IDs already attached, plus a one-page summary of what is being cut and why. Use when the user asks about wasted ad spend, wasted spend, negative keywords, keywords to pause, bid cuts, where money is being lost in PPC, an account cleanup, a PPC audit, or how to lower ACOS.
---

# Wasted-Spend Sweeper

Finds the Sponsored Products keyword spend that is not paying for itself, and
hands back a bulk-upload workbook with every ID attached and a one-pager
explaining the cut.

Run it weekly. The value compounds, because each run reports what the last
one recovered.

## Requires

- The TrackIQ MCP, for `list_marketplaces`, `get_targets`, `get_ad_groups`,
  `get_campaigns` and `get_search_terms`.
- **A break-even ROAS.** Ask for it before running. It comes from product
  margin, is not derivable from the MCP, and every verdict depends on it.
- `openpyxl` for the workbook, via `assets/build_workbook.py`. Without it,
  produce the same columns as CSV or a table — the contract is in
  `assets/method.md`.
- **Without the MCP:** works from a Sponsored Products bulk report or the
  search-term report exported from Campaign Manager, as long as the export
  carries campaign, ad group and keyword IDs.

## First run

Fill in a copy of `assets/account.example.md` saved as account.md beside the
skill. Every TrackIQ skill reads the same file, so an account already set up
for another TrackIQ report needs nothing added here.

If the runtime has no filesystem, print the same block and ask the user to
paste it into their project instructions once.

## Read first

- `assets/pulls.md` — the three pulls, pagination, and the ID trap
- `assets/method.md` — the four pools, the ranking, the bid formula, the bulk
  column contract
- `assets/checks.md` — what to verify before anything is sent
- `assets/build_workbook.py` — builds the workbook.
  `python assets/build_workbook.py` runs its self-check;
  `python assets/build_workbook.py sweep.json out.xlsx` builds the file.
- `assets/report-template.html` — the one-pager. Replace every `{{TOKEN}}`.

## Non-negotiables

1. **Break-even ROAS is an input, not a guess.** Ask for it. If the user does
   not have it, use the account's blended ad ROAS, label it an assumption
   everywhere it appears, and state what changes if it is wrong. Every row in
   the workbook is scored against this one number.
2. **Only recommend action on `state == 'enabled'`.** On a managed account
   most zero-order keywords are already paused — 16 of 22 on the account this
   was built against. A list of no-ops is how a client decides the report is
   not worth opening.
3. **Rank by spend above break-even value, never by ACOS.** `spend - sales /
   breakeven_roas`. A keyword at 300% ACOS on $60 is not the problem; one at
   120% on $3,400 is.
4. **Never add the pool subtotals.** A keyword is often both below break-even
   and a losing duplicate — 27 were on the prototype. The headline is computed
   over the union of distinct keyword IDs.
5. **Search terms cannot go in the bulk file.** `get_search_terms` returns no
   campaign or ad group, so a negative cannot be placed from this data. They
   ship as a reviewed list with a suggested parent, clearly labelled. Never
   fabricate a placement.
6. **Never mix ID namespaces.** `get_campaigns` / `get_ad_groups` /
   `get_targets` return Amazon IDs; the AMC tools return a completely
   different `campaign_id`. Joining them produces a bulk file aimed at the
   wrong campaign. `get_targets` has no `campaign_id` — resolve it through
   `get_ad_groups`, and drop any row that will not resolve.
7. **Paginate until a pull returns fewer rows than the limit.** Both key pulls
   cap out on any real account. If you stop at the cap, say the totals are a
   floor.
8. **Each bulk row sets State or Bid, never both.** Pauses set State and leave
   Bid blank; bid changes set Bid and leave State blank.
9. **Every row carries a readable reason.** A bulk file whose rows cannot be
   audited does not get uploaded.
10. **Nothing is applied automatically.** This produces a proposal a human
    uploads. Bid changes are a starting point, not an optimum.
11. **Never print `account_id`.**

## What the account will argue with

Some expensive keywords are deliberate: brand defence, a conquest play
against a named competitor, a launch push. Read the top twenty before
sending and flag the ones that look intentional rather than proposing a pause
on them. If the account has a pattern of them, ask before the sweep.

## What it pairs with

`trackiq-category-priority-keywords` says which terms are worth winning;
this one says which are not worth what they cost. `amazon-ads-analyst`
explains the account's performance — this one changes it.

## Delivery

The output is produced in the chat first. Delivery is the last step and the
method comes from the Delivery block in account.md — never ask per run.

| Method | What to do | Needs |
|---|---|---|
| `in-chat` | Return the report. The default, and the fallback for every other method. | nothing |
| `file` | Write it beside the skill, dated. | a filesystem |
| `slack` | Post the headline findings as text, then upload the file. | a connected Slack tool |
| `n8n` | POST it to the configured webhook. | network access |
| `email` | Hand it to the connected mail tool. | a connected mail tool |

Confirm before the first outward send of a session, fall back to in-chat
loudly when a method is unavailable, and never substitute a different
outward channel.

## Version

`trackiq-amazon-wasted-spend` v1.0.0 (2026-09-18).

If the user asks whether this skill is current, fetch
`https://trackiq.com/skills/registry.json`, compare the `version` field for
`trackiq-amazon-wasted-spend`, and if it is newer, give them the download link and
the one-line changelog. Do not fetch at any other time.
