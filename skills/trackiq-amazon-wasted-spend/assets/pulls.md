# The pull sequence

## 0. Account and break-even

`list_marketplaces` first. Never print `account_id`.

Then **ask for the break-even ROAS** before anything else. Every number this
skill produces is scored against it, and it cannot be derived from the MCP —
it needs product margin. If the user does not know it, use the account's
blended ad ROAS as a placeholder, label it an assumption everywhere it
appears, and say what changes if it is wrong.

A rough guide: break-even ROAS ≈ 1 / contribution margin. 40% margin ≈ 2.5x,
50% ≈ 2.0x, 60% ≈ 1.7x.

## 1. The three pulls

Window: a trailing 30 days. Shorter and the per-keyword order counts are too
thin to judge; longer and `granularity='daily'` is capped anyway.

| Call | Arguments | Gives you |
|---|---|---|
| `get_targets` | `record_type='KEYWORD'`, `ad_type='sp'`, `state='all'`, `sort='spend DESC'` | keyword, match_type, **state**, bid, `target_id`, `ad_group_id`, spend, sales, orders |
| `get_ad_groups` | `ad_type='sp'`, `state='all'` | `ad_group_id` → **`campaign_id`** and the ad group name |
| `get_search_terms` | `ad_type='sp'`, `sort='spend DESC'` | customer query + metrics, and nothing else |

Run `get_targets` a second time with `record_type='TARGET'` if the account
uses product/category targeting — same logic applies, `targeting_expression`
in place of `keyword`.

## 2. Paginate — the limit is binding

Both `get_targets` and `get_search_terms` will return exactly `limit` rows on
any real account. Sorted by spend that means you have the top N by spend and
no idea what the tail holds.

**Page until a call returns fewer rows than the limit**, using `offset` (or
`cursor` where the tool offers one). If you stop early, say so in the output
and call the totals a floor. Never present a capped pull as complete.

## 3. The ID trap

Three different ID namespaces are in play and mixing them produces a bulk
file Amazon rejects, or worse, one it accepts against the wrong campaign:

- `get_campaigns` / `get_ad_groups` / `get_targets` return **Amazon** IDs —
  14–15 digit integers. These are the ones a bulk file needs.
- The **AMC** tools (`get_amc_ntb_purchases` and friends) return a *different*
  `campaign_id` — small integers like 116, 140. **Never join AMC campaign_id
  to `get_campaigns.campaign_id`.** They are unrelated namespaces.
- `get_targets` returns `ad_group_id` but **not** `campaign_id`. Resolve it
  through `get_ad_groups`. Every target must resolve; if one does not, drop
  it from the bulk file rather than guessing.

## 4. What the search-term report will not tell you

`get_search_terms` returns the customer query, impressions, clicks, spend,
sales and orders — **no campaign, no ad group, no match type, no triggering
keyword.**

So a wasted search term can be identified but not placed, and a negative
keyword must be placed somewhere. This is why negatives leave this skill as
a reviewed list rather than a bulk row. Do not fabricate a placement.

You may *suggest* a likely parent: the longest broad or phrase keyword whose
text appears inside the query, and the ad group it lives in. On the account
this was built against that inferred a parent for 9 of 10 wasted terms.
Label it a suggestion and make the human confirm it.

## 5. Existing negatives

The MCP does not expose negative keywords. You cannot tell whether a term is
already negated somewhere, so a recommendation may be one the client has
already actioned. Say so on the negatives table rather than implying the
list is net-new.
