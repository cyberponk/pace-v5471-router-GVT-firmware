// Shared fake DOM / lite / ConfigAccess for page logic tests.
const fs = require('fs');
module.exports = function load(file, ssi) {
  // <!--#include file="x" --> -> ssi['include=x'] (empty if not given)
  const html = fs.readFileSync(file, 'utf8').replace(/<!--#include file="([^"]+)" -->/g, (m, f) => ssi['include=' + f] || '');
  let src = html.match(/<script type="text\/javascript">\n([\s\S]*?)<\/script>/)[1];
  src = src.replace(/<!--#echo jsonvar="([^"]+)"-->/g, (m, k) => { if (!(k in ssi)) throw new Error('no ssi ' + k); return ssi[k]; });
  const els = {};
  const el = id => {
    if (!els[id]) {
      if (!new RegExp('id="' + id + '"').test(html)) throw new Error('element not in page: ' + id);
      // initial innerHTML: the element's content up to its closing tag (pre/td/div)
      const body = html.match(new RegExp('id="' + id + '"[^>]*>([\\s\\S]*?)</(pre|td|div|span|small)>'));
      els[id] = { id, value: '', innerHTML: body ? body[1] : '', style: {}, onchange: null };
      const opts = [...html.matchAll(new RegExp('<select id="' + id + '"[^>]*>([\\s\\S]*?)</select>', 'g'))];
      if (opts.length) els[id].options = [...opts[0][1].matchAll(/<option value="([^"]*)">([^<]*)</g)].map(o => ({ value: o[1], text: o[2] }));
    }
    return els[id];
  };
  const ctx = { msgs: [], calls: [], handlers: {}, el };
  global.document = { getElementById: el };
  let readyFn;
  global.lite = Object.assign(sel => ({ bind: (ev, fn) => { ctx.handlers[sel] = fn; } }), {
    util: { parseJson: t => { if (t === 'undefined' || t === 'null') return undefined; return JSON.parse(t); } },
    event: { ready: fn => { readyFn = fn; } },
  });
  global.$ = global.lite;
  global.App = { MessageUtil: { clearAll: () => ctx.msgs.length = 0, info: m => ctx.msgs.push('I:' + m), error: m => ctx.msgs.push('E:' + m) } };
  global.ConfigAccess = tok => {
    const c = { w: {}, f: {}, e: {}, r: [], c: [] };
    return { rollback() { c.w = {}; c.f = {}; c.e = {}; c.r = []; c.c = []; return this; },
      write(u, v) { if (typeof u === 'string') { c.w[u] = v; } else { Object.assign(c.w, u); } return this; },
      read() { return this; }, remove(n) { c.r.push(n); return this; }, create(n) { c.c.push(n); return this; },
      encrypt(n, v) { c.e[n] = v; return this; }, fct(n) { c.f[n] = 1; return this; },
      commit(cb) { ctx.calls.push({ token: tok, write: c.w, encrypt: c.e, fct: Object.keys(c.f), remove: c.r, create: c.c }); cb({}); } };
  };
  eval(src); readyFn();
  ctx.Page = typeof Page !== 'undefined' ? Page : undefined;
  return ctx;
};
