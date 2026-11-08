import { mountDemo } from '../engine/demo.js';
import { app } from './config.js';

const root = document.querySelector('[data-splitflap-demo]');
try {
  const dispose = await mountDemo(root, app);
  window.addEventListener('pagehide', (event) => { if (!event.persisted) dispose(); });
} catch (error) {
  const message = document.createElement('p');
  message.setAttribute('role', 'alert');
  message.textContent = 'The demo could not start. ' + error.message;
  root.replaceChildren(message);
  console.error(error);
}
