# Profile Page Visual Cleanup — Design

**Date:** 2026-07-16
**Status:** Approved
**Scope:** Visual/UX restructure of `/dashboard/profile`. No API or data changes, no new features, no removed functionality (only display-only clutter is dropped).

## Problem

The profile page stacks six cards with inconsistent treatment:

- The "Personal Information" heading floats outside its card while every other card has its heading inside.
- ~12 hand-rolled inline SVGs at varying sizes and colors, while the rest of the app uses lucide-react.
- Redundant data: "Total Calls" appears in both Quick Stats and UsageChart's own stat tiles; "Daily Used" duplicates the Subscription card's daily usage bar.
- Mislabeled stat: Quick Stats "Total Projects" actually displays `generation_count` (total generations).
- Low-value clutter: raw User ID in monospace and a "Last Updated" timestamp.
- The Appearance/theme card occupies the most prominent slot (top-left) on a page about the user's profile.

## Layout

Keep the `lg:grid-cols-3` grid (2/3 left, 1/3 right). Reorganize six cards into four:

```
┌ Profile Settings ──────────────────────────┐
│ LEFT (2/3)               RIGHT (1/3)       │
│ ┌─ Profile ────────────┐ ┌─ Plan ────────┐ │
│ │ avatar + name form   │ │ tier + status │ │
│ │ email w/ verified ✓  │ │ usage bar     │ │
│ │ "member since" line  │ │ + all-time    │ │
│ └──────────────────────┘ │ limits tiles  │ │
│ ┌─ Usage ──────────────┐ │ features      │ │
│ │ stat tiles (existing)│ │ upgrade CTA   │ │
│ │ analytics chart      │ └───────────────┘ │
│ │ breakdown (existing) │ ┌─ Preferences ─┐ │
│ └──────────────────────┘ │ theme toggle  │ │
│                          └───────────────┘ │
└────────────────────────────────────────────┘
```

## Card-by-card

### Profile card (left, top) — merges Personal Information + Account Information

- Heading "Profile" rendered **inside** the card (`text-xl font-semibold`).
- Avatar upload section unchanged (behavior and validation identical).
- Email field keeps its read-only treatment; the Verified / Not Verified badge moves inline next to the email label (replaces the Account Information card's row).
- First/last name inputs and Save button unchanged.
- Card footer small print: "Member since {Month Year}" from `profile.created_at`.
- **Dropped:** raw User ID row, "Last Updated" row, and the whole Account Information card.
- ProfileForm needs `email_verified` and `created_at` — both already exist on the `UserProfile` object it receives.

### Usage card (left, bottom) — existing UsageChart, light touch

- Already contains period pills, line/bar toggle, stat tiles (Total Calls, Peak RPM, Avg RPD), chart, and breakdown-by-type. Structure unchanged.
- Replace the inline-SVG empty state with lucide `BarChart3`.
- The separate Quick Stats card is **deleted**: Total Calls was a duplicate, Daily Used duplicates the Plan card's usage bar, and Total Projects (really total generations) moves to the Plan card.

### Plan card (right, top) — SubscriptionDetailsCard, light polish

- Replace inline SVGs with lucide icons (`Clock`, `Zap`, `Check`, `AlertTriangle`).
- Add a small secondary line under the daily usage bar: "{generation_count} generations all-time" (new `totalGenerations` prop passed from the page).
- Status badge, plan name, usage bar, limits tiles, features list, billing period, cancellation notice, and upgrade/manage CTAs all unchanged.

### Preferences card (right, bottom) — relocated Appearance section

- Compact card: heading "Appearance", one-line description, `ThemeToggle` (default, non-compact variant).
- Same copy as today, trimmed to fit the narrower column.

## Consistency pass

- All hand-rolled inline SVGs on the page and touched components replaced with lucide-react equivalents (`Check`, `AlertTriangle`, `Clock`, `Zap`, `BarChart3`, `User`).
- Card headings standardized: `text-xl font-semibold text-fg`, inside the card.
- Error and loading states keep current behavior; the error card's warning SVG becomes lucide `AlertTriangle`.

## Files touched

| File | Change |
|---|---|
| `frontend/src/app/dashboard/profile/page.tsx` | New card arrangement; delete Quick Stats + Account Info JSX; pass `totalGenerations` to plan card |
| `frontend/src/components/ProfileForm.tsx` | Heading inside card, verified badge by email, member-since footer, lucide `User` avatar placeholder |
| `frontend/src/components/SubscriptionDetailsCard.tsx` | lucide icons, all-time generations line |
| `frontend/src/components/UsageChart.tsx` | lucide `BarChart3` empty state only |

## Error handling

Unchanged: profile load failure shows the retry card; analytics failure stays silent (chart empty state); form/avatar errors render inside the Profile card as today.

## Testing / verification

- `npm run lint` and `npm run build` in `frontend/`.
- Dev-server visual check: light + dark themes, `lg` two-column and mobile stacked breakpoints.
- Behavior spot-checks: avatar upload flow, profile save, analytics period switching, theme toggle.

## Out of scope

- Data-fetching refactor (moving profile/analytics to SWR hooks).
- Extracting the duplicated `UserProfile`/`Subscription` interfaces into a shared types module.
- Wiring the Upgrade Plan button (currently a no-op; stays a no-op).
- Tabbed settings layout.
