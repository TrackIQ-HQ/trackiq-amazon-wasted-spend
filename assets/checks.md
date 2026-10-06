# Before you send it

## 1. Is the arithmetic honest?

- **Break-even ROAS is stated wherever a verdict appears**, and labelled an
  assumption if the user did not supply it from margin.
- The headline is computed over the **union of distinct keyword IDs**, not by
  adding pool subtotals. Check that the keyword count is smaller than the sum
  of the pools if any keyword appears twice.
- Search-term spend is reported **beside** the headline, never inside it — it
  overlaps keyword spend completely.
- The window is stated and the run-rate arithmetic is shown, not implied.

## 2. Is every row actionable?

- **No already-paused keyword appears in a pause recommendation.** Filter on
  `state == 'enabled'` and spot-check three rows.
- Every bulk row has a Campaign ID, Ad Group ID and Keyword ID, all resolved
  and none null. Drop a row rather than ship it with a missing ID.
- Pause rows set State and leave Bid blank; bid rows set Bid and leave State
  blank. A row that does both is ambiguous and Amazon may apply either.
- No search term appears in the bulk tab. Negatives are a reviewed list.
- Every row carries a reason a human can read.

## 3. Did the pulls finish?

- **Paginate until a call returns fewer rows than the limit.** If you stopped
  at the cap, the output says the totals are a floor and names the cut.
- Every `ad_group_id` resolved to a `campaign_id`.
- No AMC campaign_id anywhere near this report — different namespace.

## 4. Would the client recognise the list?

Read the top twenty keywords. A brand term at high ACOS is often defensive
spend the client chose on purpose; a competitor term may be a deliberate
conquest play. Flag the ones that look intentional rather than silently
proposing a pause — and if the account has an obvious pattern of them, ask
before the sweep rather than after.

## 5. The deliverables agree

- The workbook's headline matches the one-pager's headline, to the dollar.
- Bulk row count in the report equals the rows in the Bulk upload tab.
- The Read me tab states the break-even used, the window, and that nothing is
  applied automatically.

## 6. Render check

```js
({ overflows: document.documentElement.scrollWidth > window.innerWidth,
   tables: document.querySelectorAll('table').length,
   rows: [...document.querySelectorAll('table')].map(t => t.querySelectorAll('tbody tr').length),
   logos: [...document.images].map(i => i.naturalWidth > 0) })
```

`overflows` false, `logos` all true, `rows` matching what you computed. Then
look at it; if it will not paint, say the check was structural.

## 7. Ship

- `<client>-wasted-spend-<YYYY-MM-DD>.xlsx` and `.html`, same date.
- Keep a record of what was proposed. **Next run, report what was actioned
  and what it recovered** — a running total of spend recovered since the
  first sweep is what turns this from a report into a retained service.
