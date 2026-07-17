# Profile Page Visual Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure `/dashboard/profile` from six inconsistent cards into four (Profile, Usage, Plan, Preferences), delete redundant data, and replace all hand-rolled inline SVGs with lucide-react icons.

**Architecture:** Pure presentational refactor of one Next.js App Router client page and three components it renders. Component changes land first (ProfileForm, SubscriptionDetailsCard, UsageChart), then the page-level restructure consumes them. No API, data-shape, or behavior changes.

**Tech Stack:** Next.js 15 (App Router, client components), Tailwind CSS with the project's Violet Glow token classes (`card`, `text-fg`, `text-muted`, `bg-card-muted`, `border-border`, `bg-brand-gradient`), lucide-react ^0.544.

**Spec:** `docs/superpowers/specs/2026-07-16-profile-page-cleanup-design.md`

## Global Constraints

- No unit-test infrastructure exists in `frontend/` (no jest/vitest, no `test` script). Per-task verification is `npx tsc --noEmit` + `npm run lint`; final task adds `npm run build` and a manual visual check.
- All commands run from `frontend/` (`/Users/jileyitayo/Documents/Projects/LandingV2/frontend`).
- Icons come from `lucide-react` (already a dependency). No new dependencies.
- Card headings: `text-xl font-semibold text-fg`, rendered **inside** the card.
- Preserve behavior exactly: avatar upload validation, profile save, analytics period switching, theme toggle, loading/error states.
- The working tree has unrelated uncommitted changes in `frontend/src/app/dashboard/page.tsx` (the projects dashboard, NOT the profile page) and `frontend/src/components/DashboardHeader.tsx`. Do not touch or commit those files.
- Commit messages end with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.

---

### Task 1: ProfileForm — heading inside card, verified badge, member-since footer, lucide avatar placeholder

**Files:**
- Modify: `frontend/src/components/ProfileForm.tsx`

**Interfaces:**
- Consumes: `initialProfile: UserProfile` (already passed by the page; `email_verified: boolean` and `created_at: string` already exist on the interface).
- Produces: ProfileForm now renders its own "Profile" card heading. Task 4 relies on this and removes the page-level "Personal Information" heading. Props are unchanged: `{ initialProfile, onUpdate }`.

- [ ] **Step 1: Add lucide import**

At the top of `frontend/src/components/ProfileForm.tsx`, after the existing imports:

```tsx
import { User } from "lucide-react";
```

- [ ] **Step 2: Add card heading**

Inside the returned `<div className="card p-6">`, insert as the first child (before the error message block):

```tsx
      <h2 className="text-xl font-semibold text-fg mb-4">Profile</h2>
```

- [ ] **Step 3: Replace the avatar placeholder SVG with lucide `User`**

Replace this block:

```tsx
                <svg
                  className="w-12 h-12 text-muted"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                </svg>
```

with:

```tsx
                <User className="w-12 h-12 text-muted" aria-hidden="true" />
```

- [ ] **Step 4: Put the verified badge next to the email label**

Replace the email label:

```tsx
          <label
            htmlFor="email"
            className="block text-sm font-medium text-fg mb-1"
          >
            Email Address
          </label>
```

with:

```tsx
          <div className="flex items-center gap-2 mb-1">
            <label htmlFor="email" className="text-sm font-medium text-fg">
              Email Address
            </label>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                initialProfile.email_verified
                  ? "bg-green-100 text-green-800 dark:bg-green-500/15 dark:text-green-400"
                  : "bg-yellow-100 text-yellow-800 dark:bg-yellow-500/15 dark:text-yellow-400"
              }`}
            >
              {initialProfile.email_verified ? "Verified" : "Not Verified"}
            </span>
          </div>
```

- [ ] **Step 5: Add member-since footer**

After the closing `</form>` tag, still inside the card div, add:

```tsx
      <p className="mt-6 pt-4 border-t border-border text-xs text-muted">
        Member since{" "}
        {new Date(initialProfile.created_at).toLocaleDateString("en-US", {
          month: "long",
          year: "numeric",
        })}
      </p>
```

- [ ] **Step 6: Verify types and lint**

Run: `npx tsc --noEmit && npm run lint`
Expected: tsc exits 0; lint reports no errors in `ProfileForm.tsx` (pre-existing warnings elsewhere are acceptable).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/ProfileForm.tsx
git commit -m "refactor: ProfileForm carries its own heading, verified badge, member-since footer

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: SubscriptionDetailsCard — lucide icons + all-time generations line

**Files:**
- Modify: `frontend/src/components/SubscriptionDetailsCard.tsx`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: new optional prop `totalGenerations?: number` on `SubscriptionDetailsCardProps`. Task 4 passes `totalGenerations={profile.generation_count}`.

- [ ] **Step 1: Add lucide imports**

At the top of `frontend/src/components/SubscriptionDetailsCard.tsx`, after `"use client";`:

```tsx
import { AlertTriangle, Check, Clock, Zap } from "lucide-react";
```

- [ ] **Step 2: Add the `totalGenerations` prop**

Update the props interface and destructuring:

```tsx
interface SubscriptionDetailsCardProps {
  subscription?: Subscription;
  currentUsed: number;
  fallbackTierName?: string;
  totalGenerations?: number;
}

export default function SubscriptionDetailsCard({
  subscription,
  currentUsed,
  fallbackTierName = "free",
  totalGenerations,
}: SubscriptionDetailsCardProps) {
```

- [ ] **Step 3: Add the all-time line under the daily usage bar**

Directly after this existing paragraph (end of the Usage Progress block):

```tsx
        <p className="text-xs text-muted mt-1">
          {dailyLimit - currentUsed > 0
            ? `${dailyLimit - currentUsed} generations remaining today`
            : "Daily limit reached"}
        </p>
```

add:

```tsx
        {typeof totalGenerations === "number" && (
          <p className="text-xs text-muted mt-0.5">
            {totalGenerations} generations all-time
          </p>
        )}
```

- [ ] **Step 4: Replace the four inline SVGs with lucide icons**

Daily Limit tile — replace the clock `<svg …>M12 8v4l3 3…</svg>` block with:

```tsx
            <Clock className="h-4 w-4 text-muted" aria-hidden="true" />
```

Per Minute tile — replace the lightning `<svg …>M13 10V3L4 14h7v7l9-11h-7z</svg>` block with:

```tsx
            <Zap className="h-4 w-4 text-muted" aria-hidden="true" />
```

Features list — replace the checkmark `<svg …>M5 13l4 4L19 7</svg>` block with:

```tsx
              <Check
                className="h-5 w-5 text-green-500 dark:text-green-400 flex-shrink-0 mt-0.5"
                aria-hidden="true"
              />
```

Cancellation notice — replace the warning-triangle `<svg …>M12 9v2m0 4h.01…</svg>` block with:

```tsx
            <AlertTriangle
              className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5"
              aria-hidden="true"
            />
```

- [ ] **Step 5: Verify types and lint**

Run: `npx tsc --noEmit && npm run lint`
Expected: tsc exits 0; no new lint errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/SubscriptionDetailsCard.tsx
git commit -m "refactor: lucide icons + all-time generations line in SubscriptionDetailsCard

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: UsageChart — lucide empty state

**Files:**
- Modify: `frontend/src/components/UsageChart.tsx`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: no interface change; props stay `{ data, isLoading, onPeriodChange, currentPeriod }`.

- [ ] **Step 1: Add lucide import**

After the recharts import block in `frontend/src/components/UsageChart.tsx`:

```tsx
import { BarChart3 } from "lucide-react";
```

- [ ] **Step 2: Replace the empty-state SVG**

Replace the bar-chart `<svg className="mx-auto h-12 w-12 text-muted" …>M9 19v-6a2 2 0 00-2-2H5…</svg>` block (inside the `chartData.length === 0` branch) with:

```tsx
              <BarChart3 className="mx-auto h-12 w-12 text-muted" aria-hidden="true" />
```

- [ ] **Step 3: Verify types and lint**

Run: `npx tsc --noEmit && npm run lint`
Expected: tsc exits 0; no new lint errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/UsageChart.tsx
git commit -m "refactor: lucide BarChart3 empty state in UsageChart

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Profile page — 4-card layout, delete Quick Stats + Account Info

**Files:**
- Modify: `frontend/src/app/dashboard/profile/page.tsx`

**Interfaces:**
- Consumes: ProfileForm's internal "Profile" heading (Task 1); `totalGenerations?: number` prop on SubscriptionDetailsCard (Task 2).
- Produces: final page layout; nothing downstream.

- [ ] **Step 1: Add lucide import**

After the existing imports in `frontend/src/app/dashboard/profile/page.tsx`:

```tsx
import { AlertTriangle } from "lucide-react";
```

- [ ] **Step 2: Replace the error-state SVG**

In the `if (error)` block, replace the warning `<svg className="mx-auto h-12 w-12 text-red-400" …>` block with:

```tsx
            <AlertTriangle className="mx-auto h-12 w-12 text-red-400" aria-hidden="true" />
```

- [ ] **Step 3: Replace the main grid content**

Replace everything from `{/* Main Grid Layout */}` down to (and including) the closing `</div>` that ends the grid — i.e., the entire `<div className="grid grid-cols-1 lg:grid-cols-3 gap-8">…</div>` block — with:

```tsx
        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Profile & Usage */}
          <div className="lg:col-span-2 space-y-6">
            <ProfileForm
              initialProfile={profile}
              onUpdate={handleProfileUpdate}
            />

            <UsageChart
              data={analyticsData}
              isLoading={analyticsLoading}
              onPeriodChange={handlePeriodChange}
              currentPeriod={analyticsPeriod}
            />
          </div>

          {/* Right Column - Plan & Preferences */}
          <div className="space-y-6">
            <SubscriptionDetailsCard
              subscription={profile.subscription}
              currentUsed={profile.current_period_generations}
              fallbackTierName={profile.subscription_tier}
              totalGenerations={profile.generation_count}
            />

            <div className="card p-6">
              <h2 className="text-xl font-semibold text-fg">Appearance</h2>
              <p className="mt-1 mb-4 text-sm text-muted">
                Choose how SiteSmith looks to you.
              </p>
              <ThemeToggle />
            </div>
          </div>
        </div>
```

This removes: the top-left Appearance card, the page-level "Personal Information" heading wrapper around ProfileForm, the Account Information card, and the Quick Stats card.

- [ ] **Step 4: Verify no dead code remains**

Check the file: the old Appearance / Account Information / Quick Stats JSX must be gone, and every remaining import is used (`ThemeToggle` is still used by the new Preferences card; `ProfileForm`, `UsageChart`, `SubscriptionDetailsCard`, `DashboardHeader` all still used).

Run: `npx tsc --noEmit && npm run lint`
Expected: tsc exits 0; no unused-import warnings for this file.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/dashboard/profile/page.tsx
git commit -m "refactor: restructure profile page into 4 cards, drop redundant stats

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Full verification — build + visual check

**Files:**
- None created or modified (verification only).

**Interfaces:**
- Consumes: all previous tasks.
- Produces: verified, shippable state.

- [ ] **Step 1: Production build**

Run from `frontend/`: `npm run build`
Expected: build succeeds; `/dashboard/profile` compiles with no type errors.

- [ ] **Step 2: Visual check in dev server**

Run: `npm run dev`, open `http://localhost:3000/dashboard/profile` (log in first if redirected).

Checklist:
- Four cards render: Profile + Usage on the left, Plan + Appearance on the right.
- Profile card: "Profile" heading inside the card, verified badge beside the email label, "Member since {Month Year}" footer.
- Plan card: "{N} generations all-time" line under the daily usage bar; Clock/Zap/Check icons render.
- No Quick Stats or Account Information cards anywhere.
- Toggle theme via the Appearance card: both light and dark render correctly (icons inherit token colors).
- Narrow the viewport below `lg`: columns stack in order Profile, Usage, Plan, Appearance.
- Behavior spot-checks: change analytics period (chart reloads), save a name edit (success message renders inside the Profile card).

- [ ] **Step 3: Report**

No commit. Report the checklist results (including anything that failed) back to the user.
