import { CLUBS } from './data.js';
import { createViews } from './views.js';
import { icons } from './icons.js';
import flapSets from './flap-sets.generated.js';
import { loadDrums } from './flaps.js';

const colours = { yellow: '#f2c230', blue: '#1f5fbf', orange: '#ee7a1f', green: '#23a05a', red: '#c8231f', white: '#eeeeea' };
export const bodyRows = CLUBS.length;

// Illustrative artwork for the three undecided main-digit wildcard flaps.
// This does not change the application JSON or define what will be printed.
export const wildcards = { digit: ['liver', 'jersey', 'boot'] };
export const drums = loadDrums(flapSets, { colours, icons, wildcards });
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
      text: 'The shared application flap sets put the main-name, main-digit, and header-name divider at flap 45 (table slot 46), before the six colours. Header digits have three repeated number blocks and seven spare slots. LION is a text placeholder. LIVER, jersey, and boot illustrate the three undecided digit wildcards; they are not finalized printed artwork. Motion is illustrative, not a calibrated motor-speed simulation.',
    },
  ],
};
