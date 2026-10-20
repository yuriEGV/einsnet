const fs = require('fs');

const gradientMock = { addColorStop: () => {} };
const ctxProxy = new Proxy({}, {
  get: (target, prop) => {
    if (prop === 'measureText') return () => ({ width: 50 });
    if (prop === 'createLinearGradient' || prop === 'createRadialGradient') return () => gradientMock;
    return () => {};
  },
  set: () => true
});

const canvasMock = {
  width: 1400,
  height: 800,
  clientWidth: 1400,
  clientHeight: 800,
  getContext: () => ctxProxy,
  addEventListener: ()=>{}
};

// Mock browser globals
global.window = {
  ...global,
  addEventListener: () => {},
  removeEventListener: () => {}
};
global.document = {
  getElementById: (id) => {
    if (id === 'network-map' || id === 'map-container') return canvasMock;
    return {
      value: id === 'search-device' ? '192.168.3.17' : '',
      checked: true,
      options: [],
      style: {},
      classList: { add: ()=>{}, remove: ()=>{}, toggle: ()=>{} },
      appendChild: () => {},
      addEventListener: ()=>{}
    };
  },
  createElement: () => ({
    appendChild: () => {},
    classList: { add: ()=>{}, remove: ()=>{}, toggle: ()=>{} },
    style: {},
    innerHTML: '',
    textContent: '',
    addEventListener: () => {}
  }),
  querySelectorAll: () => [],
  querySelector: () => null,
  addEventListener: () => {}
};
global.$ = id => global.document.getElementById(id);
global.canvas = canvasMock;
global.ctx = canvasMock.getContext('2d');
global.toast = () => {};

// Read app.js
const appCode = fs.readFileSync('app.js', 'utf8');

// Run relevant parts of app.js in a vm or mock context
const vm = require('vm');
const contextObj = {
  ...global,
  fetch: () => Promise.resolve({ ok: true, json: () => Promise.resolve({}) }),
  console,
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  Math,
  Number,
  String,
  Array,
  Object,
  Set,
  Map,
  JSON,
  Boolean,
  Promise,
  requestAnimationFrame: () => {},
  cancelAnimationFrame: () => {},
  addEventListener: () => {},
  removeEventListener: () => {}
};
contextObj.window = new Proxy(contextObj, {
  set(target, prop, value) {
    target[prop] = value;
    return true;
  },
  get(target, prop) {
    return target[prop];
  }
});
const context = vm.createContext(contextObj);

vm.runInContext(appCode, context);

// Test state
const state = context.state;
console.log("Total devices in state:", state.devices.length);

const reloj = state.devices.find(d => d.ip === '192.168.3.17');
const routerPorteria = state.devices.find(d => d.ip === '192.168.3.1');
console.log("Reloj 192.168.3.17 found:", !!reloj, "Sede:", context.getDeviceSede(reloj));
console.log("Router 192.168.3.1 found:", !!routerPorteria, "Sede:", context.getDeviceSede(routerPorteria));

// Test AutoLayout in Lynch view
state.mapSedeView = 'lynch';
context.autoLayout();

console.log("Reloj coords:", { x: reloj.x, y: reloj.y });
console.log("Router coords:", { x: routerPorteria.x, y: routerPorteria.y });

const isRelojValid = Number.isFinite(reloj.x) && Number.isFinite(reloj.y) && (reloj.x !== 0 || reloj.y !== 0);
const isRouterValid = Number.isFinite(routerPorteria.x) && Number.isFinite(routerPorteria.y) && (routerPorteria.x !== 0 || routerPorteria.y !== 0);

console.log("Reloj coords valid:", isRelojValid);
console.log("Router coords valid:", isRouterValid);

// Test isFiltered when searching for 192.168.3.17
// search-device input returns '192.168.3.17'
const relojFiltered = context.isFiltered(reloj);
const routerFiltered = context.isFiltered(routerPorteria);
const gwFiltered = context.isFiltered(state.devices.find(d => d.ip === '192.168.80.1'));
const otherDevFiltered = context.isFiltered(state.devices.find(d => d.ip === '192.168.80.22'));

console.log("When searching '192.168.3.17':");
console.log(" - Is Reloj 192.168.3.17 filtered out (hidden)?", relojFiltered, "(Must be FALSE)");
console.log(" - Is Router Porteria 192.168.3.1 filtered out (hidden)?", routerFiltered, "(Must be FALSE)");
console.log(" - Is GW Fortinet 192.168.80.1 filtered out (hidden)?", gwFiltered, "(Must be FALSE)");
console.log(" - Is unrelated PC 192.168.80.22 filtered out (hidden)?", otherDevFiltered, "(Must be TRUE)");

if (isRelojValid && isRouterValid && !relojFiltered && !routerFiltered && !gwFiltered && otherDevFiltered) {
  console.log("\n>>> ALL TESTS PASSED! Map search and layout for 192.168.3.17 is 100% functional!");
  process.exit(0);
} else {
  console.log("\n>>> TEST FAILED! Details above.");
  process.exit(1);
}
