# Devlog and in-game news: spike

2026-09-28, Web Engineer. This note is research only: no code, and nothing is published.

User ask: "Dev changelogs like news in the game, to introduce to our installed players what's upcoming and new updates, so they have something to wait for, are excited to check, and actively upgrade the game."

## Recommendation in one paragraph

Maintain one changelog file in the game repo. A script turns it into three outputs:
- a small `news.json` on the R2 city-pack host;
- the Play "What's new" text;
- a devlog page on paperskyline.org.

In the game, a paper "News" note on the title screen shows each entry as **New**, **Coming soon** or **Now available: update**. It marks unread entries with one ink dot and never blocks play. Its only action is Play's own In-App Update sheet, started by the player. There are no push notifications, no links out, no timers and no dates promised. The catch is that a build can only show news if it fetches news. If 1.0 ships without the fetch and the update check, 1.0 players only ever learn of updates through the Play Store.

## 1. The in-game news surface

- **Where.** The title screen gets a folded paper note beside Play, with an ink dot while any entry is unread. The globe needs nothing new, because cities 6–10 already show on the wishlist as "coming soon" wishes: a "Coming soon" entry can name the same city and reuse its card. Keep news off the city page, which stays about the city.
- **Layout.** One entry per page, turned like the notebook. V-D21 rules out scrolling on player-facing screens, so the note pages instead.
- **An entry.** Fields:
  - `id`
  - `kind`: `new`, `soon` or `now`
  - `title`: up to 40 characters
  - `body`: up to 200 characters, in plain words an eight-year-old can follow
  - `image`: optional, a cut from shipped art
  - `date`: month and year only
  - `version`: the version it arrived in; for `soon`, `availableIn`
- **Fetching.** Serve `news/v1/news.json` from the same R2 host as `packs/…/index.json`, and fetch it with the pack index, which the game already requests at every launch when online. That adds no new host.
  - Use a 5 s timeout, cache the last good copy, and bundle a copy in the build.
  - Images load lazily after the text.
  - A missing or broken feed shows the cache and never blocks the title screen.
  - Store the ids of read entries locally, so the "new" dot appears once per entry.

## 2. Update prompting

- **Play In-App Updates** (`com.google.play.appupdate`, Unity plugin; Android 5.0+; incompatible with .obb expansion files):
  - `GetAppUpdateInfo()` reports whether an update exists, plus its `UpdatePriority` (0–5) and `ClientVersionStalenessDays`.
  - A **flexible** update downloads in the background while the player keeps playing.
  - An **immediate** update is a full-screen update-and-restart.
  - Google's own example escalates by priority and age.
- **Our rule:**
  - Flexible only, started when the player taps "Update" on a `now` entry. Never at launch, and never as a nag.
  - Immediate only for a priority-5 fix older than 5 days, such as a broken save.
  - Set the priority for each release at upload.
- **From Coming soon to Now available:**
  - A `soon` entry carries `availableIn: "1.2.0"`.
  - While the installed version is lower and Play reports an update, the card reads **Now available: update**, and its button starts the flexible flow.
  - Once installed, the same entry reads **New**.
  - Without Play's confirmation (a sideload, or the update not rolled out yet), it stays **Coming soon**, so the card never promises something Play can't deliver.
- **Play "What's new":** up to 500 Unicode characters per language. It shouldn't be used for promotion, so generate it from the `new` entries of that version only.
- **Test:** through the internal testing track, following Google's in-app updates test guide.

## 3. One source of truth

Put `docs/news/changelog.json` in the game repo, one entry per item as in §1. `tools/news.py` (Web Engineer) writes:
1. `news.json` for R2, published with the city packs by the existing upload step (B);
2. `docs/store/google-play/whats-new/<version>.txt`, which fails if over 500 characters;
3. `devlog.html` on paperskyline.org, a static page with the same entries, newest first, that passes `tools/check.sh`.

The script keeps the three outputs in step. A human edits only the changelog.

## 4. Child-audience limits

- **Families policy.** It forbids "shocking or emotionally manipulative tactics to encourage ads viewing or in-app purchases", monetisation "not clearly distinguishable from your app content", and links to policy-violating sites. It sets no explicit parental-gate rule for plain links: its adult-action rule covers social features where children exchange personal information.
- **We go stricter:**
  - No push notifications. Android 13+ would also need a POST_NOTIFICATIONS prompt.
  - No links out of the game from the news note; the only button is Play's own update sheet.
  - No countdowns, "hurry", streaks or limited-time framing.
  - "Coming soon" never states a date.
  - The ad never appears in or next to the news.
- If a link out is ever wanted (for example to the devlog), put it behind a simple adult gate, such as holding the button while solving a small sum. That matches Apple's Kids-category practice for when iOS follows.
- **Privacy:** the downloads paragraph needs one line saying the launch request also fetches the news list. The In-App Updates library talks only to the Play Store app on the device. Check its Data safety impact when it's added.

## 5. Plan

| Task | Owner | Scope | When |
|---|---|---|---|
| N1 | Web Engineer | Changelog schema, `tools/news.py`, and `devlog.html` on the site | Can start now; the devlog page and generated Play notes can go with the first release |
| N2 | Engineer B | News fetch with the pack index, cache, read dots; In-App Updates (flexible from the card, immediate only for priority 5) | Recommend a minimal version in the first release (§ below) |
| N3 | Designer → Engineer A | The title-screen news note: paper page, New / Coming soon / Now available stamps, image slot, paging, Reduce Motion | v1.1 |
| N4 | Web Engineer + coordinator | Privacy line for the news fetch; Data safety check for the updates library | Before N2 ships |

**First Play release or later?** Only N1 is risk-free for the first release: it touches the website and the release notes, not the build. Of N2, the two runtime pieces only help the players of the build that contains them:
- the news fetch;
- the update check.

If the frozen first build can take a minimal version, a feed fetch plus a text-only note plus a flexible update button, then every 1.0 install can later hear about 1.1. If not, ship without it and accept that 1.0 players find updates through the Play Store's own auto-update and "What's new". The coordinator and the user decide, given the build freeze.

## Sources

- In-app updates: https://developer.android.com/guide/playcore/in-app-updates and the Unity guide https://developer.android.com/guide/playcore/in-app-updates/unity
- Families policy: https://support.google.com/googleplay/android-developer/answer/9893335
- Release notes, 500 characters per language: https://support.google.com/googleplay/android-developer/answer/9859348 and https://deku.posstree.com/en/share/google-play/release-notes-character-limit/
- No promotion in release notes: https://www.releasepad.io/blog/mobile-app-release-notes/ (secondary; check the Play metadata policy before relying on it)
