import { forwardPath } from './drums.js';

// The renderer supplies one abortable forward step. No league data or dimensions here.
export class MotionController {
  constructor(modules, step) {
    this.modules = modules;
    this.step = step;
    this.controller = null;
  }

  stop() {
    this.controller?.abort();
  }

  async moveTo(targets, { animate = true } = {}) {
    if (targets.length !== this.modules.length) throw new Error('Target count does not match the board.');
    this.stop(); // An interrupted step settles forward before planning the new path.
    const controller = this.controller = new AbortController();
    await Promise.all(this.modules.map(async (module, index) => {
      const path = forwardPath(module.drum, module.index, targets[index]);
      module.element?.toggleAttribute('data-unavailable', path === null);
      if (path === null) return; // Hold the actual flap; never invent an unavailable one.
      for (const next of path) {
        if (controller.signal.aborted) return;
        await this.step(module, next, { animate, signal: controller.signal });
      }
    }));
    return !controller.signal.aborted;
  }
}
