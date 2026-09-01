# Frontend track — CLAUDE.md

Scope: this folder owns the SIF-precursor dashboard. Plain HTML/CSS/JS, no
framework. See root `CLAUDE.md` for the exact API response shapes.

## Responsibilities

1. Build the dashboard against a hand-written mock JSON matching the root
   contract's `/api/dashboard/summary` shape — don't wait for backend to be
   ready
2. Show precursor density ranked by group (site/activity, whatever backend
   sends), plus the life-saving-rule breakdown
3. Once backend's endpoints are live, swap the mock fetch for a real one — the
   response shape shouldn't change, so this should be a one-line edit if the
   contract held
4. Keep `frontend/mock/dashboard_summary.json` in the repo as the mock
   fixture, so backend can diff their real response against it as a sanity
   check

## Out of scope

No modeling logic here. If a number needs to be computed rather than
displayed, that's a backend job — ask for a new field in
`/api/dashboard/summary` instead of computing it client-side.
