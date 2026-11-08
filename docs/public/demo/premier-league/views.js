import { EARLY, END, GAMES, FIXTURES } from "./data.js";
// Kept close to the mockup so view changes remain easy to port.
const M = "−";
export function createViews(state, bodyRows) {

  function num(n) {
    if (n < 0) { const a = -n; if (a < 10) return [M, String(a)]; if (a < 60) return [M + Math.floor(a / 10), String(a % 10)]; return ["", "?"]; }
    if (n < 10) return ["", String(n)];
    if (n < 200) return [String(Math.floor(n / 10)), String(n % 10)];
    return ["", "?"];
  }
  const score = s => s == null ? ["", ""] : ["", String(s)];
  function time(t) { // "t17:30" in UK time -> [hour flap, minute flap]
    let [h, m] = t.slice(1).split(":").map(Number);
    if (state.clock === "12") { h = h - 5; if (h < 0) h += 24; h = h % 12 || 12; }
    return [String(h), ":" + String(m).padStart(2, "0")];
  }
  const dg = d => typeof d === "string" ? time(d) : d;
  const pad = rows => { while (rows.length < bodyRows) rows.push(["", "", ""]); return rows; };
  const table = () => state.season === "early" ? EARLY : END;
  const mw = () => state.season === "early" ? ["", "8"] : ["3", "8"];

  function zone(pos) {
    const end = state.season === "end";
    if (end && pos === 1) return "c:yellow";
    if (pos <= 4) return "c:blue"; if (pos === 5) return "c:orange"; if (pos === 6) return "c:green"; if (pos >= 18) return "c:red";
    return "";
  }
  function live(n, perGame) {
    const rows = [];
    GAMES.slice(0, n).forEach((g, i) => {
      if (perGame === 4 && i > 0) rows.push(["|divider", "|divider", "|divider"]);
      if (perGame >= 3) rows.push([g[0], ...dg(g[1])]);
      rows.push([g[2], ...score(g[3])]); rows.push([g[4], ...score(g[5])]);
    });
    return pad(rows);
  }

  const blk = (st, d, h, hs, a, as) => [[st, ...d], [h, ...score(hs)], [a, ...score(as)]];
  const GA = r => r[3] - r[2];
  const PLAYED_EARLY = { "EVERTON": 7, "FULHAM": 7 };
  const stand = (label, title, header, val, caption) => ({ g: "stand", label, title, seasonal: true,
    build: () => ({ header: typeof header === "function" ? header() : header, rows: table().map((r, i) => [r[0], ...val(r, i)]), caption }) });

  const VIEWS = {
    pts: stand("Points", "Standings: points", () => ["MATCHWEEK", ...mw()], r => num(r[1]),
      "The everyday view. Header shows the matchweek; each row shows a club and its points."),
    gd: stand("Goal difference", "Standings: goal difference", ["GOAL DIFFERENCE", "", ""], r => num(r[2]),
      "Negative values use the − flap (−1 to −9) or the squeezed −5 … −1 tens flaps (−10 to −59). Switch to End of season to see −49 and −58; below −59 a row shows ?. The header label tells viewers this isn't points."),
    gf: stand("Goals for", "Standings: goals for", ["GOALS FOR", "", ""], r => num(r[3]),
      "Same layout as points. GOALS FOR is in the header name set. 100+ goals would use the 10 flap on the left module."),
    ga: stand("Goals against", "Standings: goals against", ["GOALS AGAINST", "", ""], r => num(GA(r)),
      "Goals conceded. Sorted by league position, so the numbers rise towards the bottom. GOALS AGAINST is in the header name set."),
    pl: stand("Played", "Standings: played", ["PLAYED", "", ""], r => num(state.season === "early" ? (PLAYED_EARLY[r[0]] || 8) : 38),
      "Games played. Mostly useful early in the season or after postponements, when clubs are on different counts (Everton and Fulham here)."),
    mov: stand("Movement", "Standings: movement", () => ["MATCHWEEK", ...mw()], r => r[4] === "=" ? ["=", ""] : [r[4][0], r[4].slice(1)],
      "Places gained or lost since last matchweek: arrow on the left module, places on the right. Could run as a short flash after the table re-sorts."),
    zones: stand("Zones", "Standings: zones", ["PREMIER LEAGUE", "", ""], (_, i) => { const z = zone(i + 1); return [z, z]; },
      "Colour flaps on both digit modules: Champions League blue, Europa orange, Conference green, relegation red, and champions yellow at the end. Points are hidden while this shows, so it suits a short flash between views."),

    l1: { g: "live", label: "1 game (12:30)", title: "Live: the early game",
      build: () => ({ header: ["LIVE", "", ""], rows: pad([
        ...blk("2ND HALF", ["6", "7"], "LIVERPOOL", 2, "ARSENAL", 1), ["|divider", "|divider", "|divider"],
        ["GOAL!", "2", "3"], ["LIVERPOOL", "", ""], ["GOAL!", "4", "1"], ["ARSENAL", "", ""],
        ["RED CARD", "5", "8"], ["ARSENAL", "", ""], ["GOAL!", "6", "4"], ["LIVERPOOL", "", ""],
        ["|divider", "|divider", "|divider"], ...blk("KICK OFF", time("t15:00"), "BRENTFORD", null, "FULHAM", null)]),
        caption: "One game, so the spare rows can carry an event log: event and minute, then the club, 2 rows per event. Below it, the next kick-off. Printed flaps can't show player names, so the log shows who and when, not the scorer." }) },
    l4g: { g: "live", label: "4 games (3 pm)", title: "Live: the 3 pm group",
      build: () => ({ header: ["LIVE", "", ""], rows: pad([
        ...blk("2ND HALF", ["5", "9"], "BRENTFORD", 1, "FULHAM", 2), ...blk("2ND HALF", ["5", "9"], "EVERTON", 0, "SUNDERLAND", 0),
        ...blk("2ND HALF", ["6", "0"], "NOTT'M FOREST", 3, "IPSWICH TOWN", 1), ...blk("GOAL!", ["5", "8"], "HULL CITY", 1, "COVENTRY CITY", 1),
        ["|divider", "|divider", "|divider"], ...blk("KICK OFF", time("t17:30"), "MAN CITY", null, "CHELSEA", null)]),
        caption: "A typical Saturday 3 pm group, 3 rows per game, with the late kick-off waiting below a divider. 16 rows used." }) },
    l3: { g: "live", label: "6 games", title: "Live: 6 games, 3 rows each",
      build: () => ({ header: ["LIVE", "", ""], rows: live(6, 3),
        caption: "Status row (status on the name, minute on the digits), then home and away with scores. 6 games, 2 spare rows. The status row separates games, so no divider is needed." }) },
    l4: { g: "live", label: "5 games + dividers", title: "Live: 4 rows per game",
      build: () => ({ header: ["LIVE", "", ""], rows: live(5, 4),
        caption: "Adds the divider bar between games: 5 games instead of 6. Compare with 6 games to judge whether the divider earns its row." }) },
    l2: { g: "live", label: "10 games", title: "Live: 2 rows per game",
      build: () => ({ header: ["LIVE", "", ""], rows: live(10, 2),
        caption: "All 10 games on one screen, but no minute or status per game and the pairs run together. Only works when every game is in the same state, with the header carrying it." }) },
    res: { g: "live", label: "Results", title: "Results",
      build: () => ({ header: ["RESULTS", "", ""], rows: pad(GAMES.flatMap(g => [[g[2], ...score(g[6])], [g[4], ...score(g[7])]])),
        caption: "Full-time scores, 2 rows per game: the header says RESULTS, so no status row is needed and the whole matchweek fits." }) },
    fix: { g: "live", label: "Fixtures", title: "Fixtures",
      build: () => {
        const F = FIXTURES;
        const rows = []; F.forEach(f => { if (f.length === 1) rows.push([f[0], "", ""]); else { rows.push([f[0], ...time(f[2])]); rows.push([f[1], "", ""]); } });
        return { header: ["FIXTURES", "", ""], rows: pad(rows),
          caption: "Day rows, then each fixture as home (with kick-off time) and away. Saturday and Sunday fill 18 rows; Monday's game would go on a second page. Toggle the clock to see 12-hour Eastern times." };
      } },

    fa: { g: "cups", label: "FA Cup live", title: "FA Cup, live",
      build: () => ({ header: ["FA CUP", "R", "4"], rows: pad([
        ...blk("EXTRA TIME", ["10", "4"], "LIVERPOOL", 2, "OPPONENT", 2), ...blk("PENALTIES", ["", ""], "ARSENAL", 4, "OPPONENT", 3),
        ...blk("FULL TIME", ["", ""], "MAN CITY", 3, "HULL CITY", 1), ...blk("KICK OFF", time("t19:45"), "CHELSEA", null, "OPPONENT", null),
        ...blk("POSTPONED", ["", ""], "EVERTON", null, "OPPONENT", null)]),
        caption: "Header shows competition and round. Extra time reaches minute 104 with the 10 flap. During PENALTIES the digits show the shootout score, so the match score isn't visible. MAN CITY v HULL CITY is two EPL clubs, so both names show." }) },
    fadraw: { g: "cups", label: "FA Cup draw", title: "FA Cup draw",
      build: () => ({ header: ["FA CUP", "R", "5"], rows: pad([
        ["ARSENAL", "", ""], ["OPPONENT", "", ""], ["LEEDS UNITED", "", ""], ["LIVERPOOL", "", ""], ["OPPONENT", "", ""], ["MAN CITY", "", ""],
        ["CHELSEA", "", ""], ["OPPONENT", "", ""], ["NEWCASTLE", "", ""], ["OPPONENT", "", ""], ["OPPONENT", "", ""], ["BRIGHTON", "", ""]]),
        caption: "The next round's ties involving EPL clubs, home first, 2 rows per tie. Without a status row the pairs run together; a divider between ties would cost 5 more rows." }) },
    fafinal: { g: "cups", label: "FA Cup final", title: "FA Cup final",
      build: () => ({ header: ["FA CUP FINAL", "", ""], rows: pad([
        ...blk("FULL TIME", ["", ""], "MAN CITY", 1, "CHELSEA", 1), ["|divider", "|divider", "|divider"],
        ...blk("PENALTIES", ["", ""], "MAN CITY", 4, "CHELSEA", 5), ["|divider", "|divider", "|divider"],
        ["CHELSEA", "", "#trophy"]]),
        caption: "A one-off final: the 120-minute score and the shootout as separate blocks, then the winner with the trophy flap." }) },
    lcsf: { g: "cups", label: "League Cup semi", title: "League Cup semi-final, 2nd leg",
      build: () => ({ header: ["LEAGUE CUP SF", "L", "2"], rows: pad([
        ...blk("2ND HALF", ["8", "1"], "ARSENAL", 1, "NEWCASTLE", 1), ...blk("AGGREGATE", ["", ""], "ARSENAL", 3, "NEWCASTLE", 2),
        ["|divider", "|divider", "|divider"], ...blk("HALF TIME", ["", ""], "LIVERPOOL", 0, "OPPONENT", 0), ...blk("AGGREGATE", ["", ""], "LIVERPOOL", 1, "OPPONENT", 2)]),
        caption: "Two-legged semis: tonight's score, then the aggregate, 6 rows per tie. Both semis fit with a divider." }) },
    uclt: { g: "cups", label: "UCL league phase", title: "Champions League: league phase",
      build: () => ({ header: ["UCL MATCHDAY", "", "6"], rows: pad([["ARSENAL", "", "2"], ["LIVERPOOL", "", "5"], ["MAN CITY", "1", "1"], ["CHELSEA", "1", "9"], ["NEWCASTLE", "2", "7"]]),
        caption: "Where each English club sits in the 36-team league phase table. 1–8 go straight to the last 16, 9–24 to the play-off, 25–36 are out. The header could alternate between UCL MATCHDAY 6 and POSITION so the number is clear; zone colours could flash the three bands." }) },
    ucl: { g: "cups", label: "UCL last 16", title: "Champions League last 16, 2nd leg",
      build: () => ({ header: ["UCL LAST 16", "L", "2"], rows: pad([
        ...blk("2ND HALF", ["7", "8"], "ARSENAL", 1, "OPPONENT", 0), ...blk("AGGREGATE", ["", ""], "ARSENAL", 3, "OPPONENT", 2),
        ...blk("HALF TIME", ["", ""], "LIVERPOOL", 0, "OPPONENT", 1), ...blk("AGGREGATE", ["", ""], "LIVERPOOL", 2, "OPPONENT", 2),
        ...blk("KICK OFF", time("t20:00"), "MAN CITY", null, "OPPONENT", null)]),
        caption: "Each game is followed by an AGGREGATE block: 6 rows per tie, 3 ties at most. An alternative is to alternate the score rows between tonight's score and the aggregate." }) },
    thu: { g: "cups", label: "Thursday: UEL + UECL", title: "Thursday night: Europa and Conference",
      build: () => ({ header: ["UEL MATCHDAY", "", "3"], rows: pad([
        ...blk("2ND HALF", ["5", "5"], "ASTON VILLA", 2, "OPPONENT", 0), ...blk("1ST HALF", ["3", "1"], "TOTTENHAM", 0, "OPPONENT", 0),
        ["|divider", "|divider", "|divider"], ["CONFERENCE LEAGUE", "", ""], ...blk("2ND HALF", ["5", "2"], "CRYSTAL PALACE", 1, "OPPONENT", 1)]),
        caption: "Europa and Conference League games are both on Thursday, but the header shows one competition. Options: competition names in the main name set (CONFERENCE LEAGUE as a row, as here), or alternate pages, one per competition." }) },
    cs: { g: "cups", label: "Community Shield", title: "Community Shield",
      build: () => ({ header: ["COMMUNITY SHIELD", "", ""], rows: pad([
        ...blk("FULL TIME", ["", ""], "LIVERPOOL", 2, "CRYSTAL PALACE", 2), ["|divider", "|divider", "|divider"],
        ...blk("PENALTIES", ["", ""], "LIVERPOOL", 2, "CRYSTAL PALACE", 3), ["|divider", "|divider", "|divider"], ["CRYSTAL PALACE", "", "#trophy"]]),
        caption: "The season opener in August: no extra time, straight to penalties. Same one-off layout as the FA Cup final." }) },

    intl: { g: "other", label: "International break", title: "International break",
      build: () => ({ header: ["INTERNATIONAL BREAK", "", ""], rows: EARLY.map(r => [r[0], ...num(r[1])]),
        caption: "No club games for about two weeks, so the table stays up with a header that says why. The longest header so far; see the squeeze list." }) },
    off: { g: "other", label: "Off-season", title: "Off-season countdown",
      build: () => ({ header: ["SEASON STARTS IN", "4", "2"], rows: END.map(r => [r[0], ...num(r[1])]),
        caption: "Last season's final table with a countdown in days." }) }
    ,
    pzone: { g: "pat", label: "Zone flash", title: "Pattern: zone flash", seasonal: true,
      build: () => {
        const t = table().map(r => [r[0], ...num(r[1])]);
        const z = table().map((r, i) => { const c = zone(i + 1); return c ? [c, c, c] : [r[0], ...num(r[1])]; });
        return { header: ["PREMIER LEAGUE", "", ""], frames: [t, z], still: 1, ms: 2200,
          caption: "The table, then the zone rows turn fully into their colour and back. Whole rows read from across the room better than coloured digits alone. Switch to End of season for the champions' yellow." };
      } },
    pchamp: { g: "pat", label: "Champions", title: "Pattern: champions",
      build: () => {
        const Y = Array.from({ length: bodyRows }, () => ["c:yellow", "c:yellow", "c:yellow"]);
        const YH = ["c:yellow", "c:yellow", "c:yellow"], PL = ["PREMIER LEAGUE", "", ""];
        const f2 = Y.map((r, i) => i === 9 ? ["LIVERPOOL", "", "#trophy"] : r);
        const f3 = END.map(r => [r[0], ...num(r[1])]); f3[0] = ["LIVERPOOL", "", "#trophy"];
        return { header: PL, hframes: [YH, YH, PL, PL], frames: [Y, f2, f2, f3], still: 1, ms: 1500,
          caption: "Title clinched: the board goes yellow, the champions appear in the middle with the trophy, then the final table." };
      } },
    pgoal: { g: "pat", label: "Goal wave", title: "Pattern: goal wave",
      build: () => {
        const fr = [];
        for (let k = 0; k < bodyRows; k += 2) fr.push(Array.from({ length: bodyRows }, (_, i) => (i >= k && i < k + 3) ? ["c:red", "c:red", "c:red"] : ["", "", ""]));
        const hold = Array.from({ length: bodyRows }, () => ["c:red", "c:red", "c:red"]);
        hold[8] = ["GOAL!", "6", "7"]; hold[9] = ["LIVERPOOL", "", "2"]; hold[10] = ["ARSENAL", "", "1"];
        fr.push(hold, hold, hold);
        const LV = ["LIVE", "", ""], RD = ["c:red", "c:red", "c:red"];
        return { header: LV, hframes: fr.map((_, k) => k === 0 ? RD : k >= 10 ? RD : LV), frames: fr, still: 10, ms: 450,
          caption: "A red band rolls down the board in the scoring club's colour, then the game sits in the middle on a red field. The real speed depends on how fast the drums turn, so this is a visual sequence, not a hardware timing estimate." };
      } },
    prain: { g: "pat", label: "Rainbow", title: "Pattern: rainbow bands",
      build: () => {
        const P = ["c:red", "c:orange", "c:yellow", "c:green", "c:blue", "c:white"];
        const fr = P.map((_, f) => Array.from({ length: bodyRows }, (_, i) => { const c = P[(i + 6 - f) % 6]; return [c, c, c]; }));
        return { header: ["c:red", "c:red", "c:red"], frames: fr, hframes: P.map((_, f) => { const c = P[(11 - f) % 6]; return [c, c, c]; }), ms: 900,
          caption: "All six colours in repeating bands, scrolling down a row each step. Needs all six colours on the name drum." };
      } },
    pcheck: { g: "pat", label: "Checker", title: "Pattern: checker",
      build: () => {
        const f = sh => Array.from({ length: bodyRows }, (_, i) => { const a = (i + sh) % 2 ? "c:red" : "c:white", b = (i + sh) % 2 ? "c:white" : "c:red"; return [a, b, a]; });
        return { header: ["", "", ""], frames: [f(0), f(1)], ms: 1200,
          caption: "Alternating colours across the three columns. The wide name column dominates, so vertical patterns look lopsided; horizontal bands work better." };
      } },
    pflags: { g: "pat", label: "Flags", title: "Pattern: flags",
      build: () => {
        const bands = cs => Array.from({ length: bodyRows }, (_, i) => { const c = cs[Math.min(cs.length - 1, Math.floor(i * cs.length / bodyRows))]; return [c, c, c]; });
        const ger = bands(["", "c:red", "c:yellow"]), ned = bands(["c:red", "c:white", "c:blue"]), ukr = bands(["c:blue", "c:yellow"]);
        const irl = Array.from({ length: bodyRows }, () => ["c:green", "c:white", "c:orange"]);
        return { header: ["INTERNATIONAL BREAK", "", ""], frames: [ger, ned, ukr, irl], ms: 2500,
          caption: "Germany (the black band is blank flaps), the Netherlands, Ukraine, then Ireland across the columns. Horizontal-stripe flags work; vertical ones are distorted by the wide name column, and crosses (England, Scotland) can't be drawn." };
      } }
  };


return Object.fromEntries(Object.entries(VIEWS).map(([id, view]) => [id, {
  ...view, build() {
    const model = view.build();
    const rows = model.frames || [model.rows];
    return { ...model, frames: rows.map((frame, index) => [model.hframes?.[index] || model.header, ...frame]) };
  },
}]));
}
