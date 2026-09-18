# Method

Four pools, in the order they are usually worth money. The obvious one —
keywords that spent and sold nothing — is normally the smallest.

On the account this was built against: zero-order keywords held $466,
below-break-even keywords $45,852, losing duplicate copies $13,889, and
wasted search terms $628. **Lead with duplicates and bids, not negatives.**

## Pool 1 — spent, sold nothing, still enabled

```
orders == 0  and  spend >= floor  and  state == 'enabled'
```

**The state filter is not optional.** Most zero-order keywords on a managed
account are already paused — 16 of 22 on the prototype. Recommending a pause
on an already-paused keyword is a no-op, and a list full of them is how a
client decides the report is not worth reading.

Floor: $50 over 30 days by default. Below that the row costs more attention
than it saves.

Action: **pause**. Exact — the keyword ID is known.

## Pool 2 — below break-even

```
orders > 0  and  spend >= floor  and  sales / spend < breakeven_roas
```

Rank by **spend above break-even value**, not by ACOS:

```
excess = spend - (sales / breakeven_roas)
```

A keyword at 300% ACOS on $60 matters less than one at 120% on $3,400. ACOS
sorting puts the small disaster first; this puts the expensive one first.

Action: **cut the bid**, do not pause. These keywords convert — they are
priced wrong. Scale the existing bid by how far short of break-even it came,
floored at a 50% cut:

```
new_bid = round(bid * max(0.5, roas / breakeven_roas), 2)
```

That is a starting point, not an optimum, and the output must say so.

## Pool 3 — duplicated keywords bidding against each other

Group enabled keywords by `(lowercased text, match_type)`. Where a group has
more than one placement with spend:

- the **winner** is the placement with the highest ROAS
- **losers** are the others that fall below break-even and clear the floor
- only act when the winner is itself at or above break-even — if every copy
  loses money, that is Pool 2, not a consolidation

Action: **pause the losers, keep the winner.** This is usually the strongest
line in the report, because pausing a loser does not reduce reach — the
winning ad group already covers that keyword. It moves budget from a copy
that loses money to one that makes it.

On the prototype, *patio string lights* on exact ran in nine ad groups, one at 3.46x
and five below break-even holding $5,502 between them.

## Pool 4 — wasted search terms

```
orders == 0  and  spend >= floor
```

Action: **negative keyword — as a reviewed list, never a bulk row.** The
search-term report carries no campaign or ad group, so the placement is not
in the data. See `assets/pulls.md`.

Suggest a parent where one can be inferred, label it a suggestion, and note
that existing negatives are not visible to this skill so some rows may
already be actioned.

## No double counting

A keyword can be in Pool 2 and Pool 3 at once — on the prototype, 27 of them
were. Compute the headline over the **union of distinct keyword IDs**:

```
recoverable = sum(spend over union) - sum(sales over union) / breakeven_roas
```

Never add the pool subtotals together. Search terms overlap keyword spend
entirely and are reported beside the headline, never inside it.

## The bulk file

Amazon Sponsored Products bulk operations, one row per change:

| Column | Value |
|---|---|
| Product | `Sponsored Products` |
| Entity | `Keyword` |
| Operation | `update` |
| Campaign ID / Ad Group ID / Keyword ID | Amazon IDs, resolved per `assets/pulls.md` |
| Keyword Text / Match Type | as returned |
| State | `paused` for Pools 1 and 3; **blank** for a bid change |
| Bid | the new bid for Pool 2; **blank** for a pause |
| TrackIQ reason | one line saying why — never ship a row a human cannot audit |

Keep the reason column. A bulk file whose rows cannot be explained does not
get uploaded.

## What this skill never does

It does not apply anything. It produces a reviewed proposal with the IDs
already attached, and a human uploads it. That is the line every TrackIQ
skill holds, and it is why an agency will run this unattended.
