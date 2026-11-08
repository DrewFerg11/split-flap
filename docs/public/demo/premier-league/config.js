import { CLUBS } from './data.js';
import { createViews } from './views.js';
import { icons } from './icons.js';

const colours = { yellow: '#f2c230', blue: '#1f5fbf', orange: '#ee7a1f', green: '#23a05a', red: '#c8231f', white: '#eeeeea' };
const colourFlaps = Object.keys(colours).map((colour) => 'c:' + colour);
const days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'];
const minus = '−';
const stages = ['MATCHDAY', 'PLAY-OFF', 'LAST 16', 'QF', 'SF', 'FINAL'];
const headerNumbers = ['', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'R', 'L'];
export const bodyRows = CLUBS.length;

// TODO: consume application-owned flap data after applications/premier-league is migrated.
// Snapshot: flap-sets.md, 2026-11-05. Slot 46 is the divider on the three drums that carry it.
export const drums = {
  name: {
    label: 'Main name',
    flaps: ['', ...CLUBS, 'OPPONENT', 'KICK OFF', '1ST HALF', 'HALF TIME', '2ND HALF',
      'EXTRA TIME', 'PENALTIES', 'FULL TIME', 'AGGREGATE', 'POSTPONED', 'GOAL!', 'VAR CHECK',
      'NO GOAL', 'RED CARD', ...days, 'EUROPA LEAGUE', 'CONFERENCE LEAGUE', '@open', '|divider', ...colourFlaps],
  },
  digit: {
    label: 'Main digit',
    flaps: ['', ...[5, 4, 3, 2, 1].map((n) => minus + n), minus,
      ...Array.from({ length: 24 }, (_, n) => String(n)), ':00', ':15', ':30', ':45',
      '↑', '↓', '=', '?', '#ball', '#lion', '#trophy', '#liver', '#jersey', '#boot', '|divider', ...colourFlaps],
  },
  hname: {
    label: 'Header name',
    flaps: ['', 'PREMIER LEAGUE', 'MATCHWEEK', 'LIVE', 'RESULTS', 'FIXTURES', 'POINTS',
      'GOAL DIFFERENCE', 'GOALS FOR', 'GOALS AGAINST', 'PLAYED', 'POSITION',
      'FA CUP', 'FA CUP QF', 'FA CUP SF', 'FA CUP FINAL', 'LEAGUE CUP', 'LEAGUE CUP QF',
      'LEAGUE CUP SF', 'LEAGUE CUP FINAL', ...['UCL', 'UEL', 'UECL'].flatMap((cup) => stages.map((stage) => cup + ' ' + stage)),
      'COMMUNITY SHIELD', 'SUPER CUP', 'CLUB WORLD CUP', 'FRIENDLY', 'INTERNATIONAL BREAK',
      'SEASON STARTS IN', '@open', '|divider', ...colourFlaps],
  },
  hdigit: {
    label: 'Header digit',
    flaps: [...headerNumbers, ...headerNumbers, ...headerNumbers, ...Array(7).fill('@open'), ...colourFlaps],
  },
};
const modules = (header = false) => [
  { type: 'name', drum: header ? 'hname' : 'name' },
  { type: 'digit', drum: header ? 'hdigit' : 'digit' },
  { type: 'digit', drum: header ? 'hdigit' : 'digit' },
];
export const layout = {
  rowHeight: 74, padding: 12,
  types: {
    name: { width: 211, flapWidth: 200, flapHeight: 42, faceWidth: 187.7, showSqueeze: true },
    digit: { width: 43, flapWidth: 33, flapHeight: 42, faceWidth: 30, multiFaceWidth: 26.6 },
  },
  rows: [{ label: 'H', header: true, modules: modules(true) },
    ...Array.from({ length: bodyRows }, (_, index) => ({ label: String(index + 1), modules: modules() }))],
};

export const app = {
  id: 'premier-league',
  description: 'A header plus ' + bodyRows + ' club rows, at the mockup’s physical proportions. All numbers are invented samples. Each module can show only its printed flaps and turns forward through its drum.',
  drums, layout, colours, icons, stepMs: 35,
  typography: {
    family: 'League Gothic',
    reference: { text: 'CRYSTAL PALACE', width: 187.7, squeeze: 0.93 },
    description: 'League Gothic measured at the real flap height, squeezed sideways to fit the face. CRYSTAL PALACE is calibrated to 93% on the 187.7 mm name face.',
  },
  defaults: { view: 'pts', season: 'early', clock: '24', zoom: 'fit', anim: 'on', marks: 'on' },
  groups: [['stand', 'Standings'], ['live', 'Matchday'], ['cups', 'Cups, Europe'], ['other', 'Other'], ['pat', 'Colour patterns']],
  options: [
    { id: 'season', label: 'Samples', values: [['early', 'Early season'], ['end', 'End of season']] },
    { id: 'clock', label: 'Kick-off times', values: [['24', '24-hour UK'], ['12', '12-hour Eastern']] },
    { id: 'zoom', label: 'Board size', values: [['fit', 'Fit board'], ['large', 'Large']] },
    { id: 'anim', label: 'Motion', values: [['on', 'Animate'], ['off', 'Still']] },
    { id: 'marks', label: 'Validation', values: [['on', 'Show flap checks'], ['off', 'Hide checks']] },
  ],
  createViews: (state) => createViews(state, bodyRows),
  notes: [
    {
      title: 'Live layouts compared',
      text: 'A status row separates games and carries the match minute. More rows per game mean fewer games fit on one page.',
      table: {
        columns: ['Rows/game', 'Games/page', 'Trade-off'],
        rows: [[2, Math.floor(bodyRows / 2), 'No individual status or minute'],
          [3, Math.floor(bodyRows / 3), 'Status, home, away'],
          [4, Math.floor((bodyRows + 1) / 4), 'A divider between games']],
      },
    },
    {
      title: 'Planned flap sets',
      text: 'The November 5 plan puts the main-name, main-digit, and header-name divider at slot 46, before the six colours. Header digits have three repeated number blocks and seven spare slots. Symbols labelled LION and LIVER are text placeholders. Motion is illustrative, not a calibrated motor-speed simulation.',
    },
  ],
};
