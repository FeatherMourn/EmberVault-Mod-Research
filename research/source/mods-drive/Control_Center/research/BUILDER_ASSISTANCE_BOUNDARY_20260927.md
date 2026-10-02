# Builder assistance boundary

## Available now

- Import catalog records from JSON.
- Search by name, ID, category, and tags.
- Maintain favorites across sessions.
- Create named offline build plans.
- Calculate material totals for a plan.
- Save and restore favorites and plans atomically.

## Deliberately not claimed

- Automatic placement in the game.
- Camera or cursor control.
- Collision bypass.
- Build-zone or multiplayer-authority changes.
- New building geometry.

The current builder layer is a safe planning/catalog surface. Runtime
placement should be researched as a separate feature with fresh-session
evidence and rollback, especially for multiplayer or world-persistence
behavior.
