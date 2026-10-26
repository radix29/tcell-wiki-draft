#!/usr/bin/env node
// How does a published wiki page render on a phone, and in a browser with no JavaScript?
//
// This is the measuring stick behind PLAN.md Phase 7 T7.2 ("mobile/terminal rendering spot check of
// tables - wide tables are the usual casualty"). It is deliberately not a gate and not in CI: it needs
// a real Chrome, and the numbers it prints are a spot check a human reads, the same kind of evidence
// as the anonymous `curl` of a rendered page in AGENTS.md. Run it against the live draft wiki:
//
//   node tools/viewport-probe.cjs https://github.com/radix29/tcell-wiki-draft/wiki/Function-Reference \
//       --width=375 --height=812 --control
//
// What it reports per page: whether the document scrolls sideways at all, and for every table the
// width of its box against the width of its content. GitHub's wiki stylesheet gives markdown tables
// `display: block; overflow-x: auto`, so a wide table never widens the page and never clips a cell:
// it becomes a box the reader drags sideways inside. `content` is the width that drag reaches, and
// it is the number to watch when adding a column to a table.
//
// --control appends a synthetic table whose first cell is one unbreakable word (--token=N chars,
// default 80) before measuring. That is the positive control: it shows the probe reports a too-wide
// table when one exists, so a page reporting none means the tables fit rather than that the probe is
// blind. Measured on 2026-10-26 the control does *not* wrap: inside a scroll box the table is laid out
// at its preferred width, which is why nothing on these pages ever breaks a word mid-token.
//
// --expr-file runs your own expression in the page instead, for anything else worth measuring; it is
// evaluated after the load event plus --wait milliseconds.
//
// Chrome flags this tool needs: headless, and a debugging port, which it supplies itself. Nothing is
// installed and nothing is downloaded. Exit 0 = measured (fit or not), 1 = a table overflowed the
// *page* (the defect worth fixing), 2 = could not measure.
const { spawn, spawnSync } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");

const args = process.argv.slice(2);
const urls = args.filter((a) => !a.startsWith("--"));
const flag = (name, dflt) => {
  const hit = args.find((a) => a.startsWith(`--${name}=`));
  return hit === undefined ? dflt : hit.slice(name.length + 3);
};
const has = (name) => args.some((a) => a === `--${name}` || a.startsWith(`--${name}=`));
const width = Number(flag("width", 375));
const height = Number(flag("height", 812));
const wait = Number(flag("wait", 1800));
const token = has("control") ? Number(flag("token", 80)) : 0;
const exprFile = has("expr-file") ? flag("expr-file") : null;
const CHROME = flag("chrome", process.env.CHROME ||
  ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
    .find((c) => spawnSync("which", [c]).status === 0) || "google-chrome");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const REPORT = `(function (token) {
  var md = document.querySelector('.markdown-body');
  if (!md) return { error: 'no .markdown-body on this page' };
  if (token) {
    var t = document.createElement('table');
    t.id = 'viewport-control-table';
    t.innerHTML = '<tr><th>ctl</th><th>col</th></tr><tr><td>' + 'a'.repeat(token) +
      '</td><td>short text here</td></tr>';
    md.appendChild(t);
  }
  var docW = document.documentElement.scrollWidth;
  var tables = [].slice.call(md.querySelectorAll('table')).map(function (t, i) {
    var longestWord = 0, longestWordText = '', widestCell = 0, widestCellText = '';
    [].slice.call(t.rows).forEach(function (row) {
      [].slice.call(row.cells).forEach(function (c) {
        var txt = (c.textContent || '').trim();
        if (c.scrollWidth > widestCell) { widestCell = c.scrollWidth; widestCellText = txt.slice(0, 34); }
        txt.split(/\\s+/).forEach(function (w) {
          if (w.length > longestWord) { longestWord = w.length; longestWordText = w.slice(0, 34); }
        });
      });
    });
    return { i: i + 1, control: t.id === 'viewport-control-table',
             cols: t.rows[0] ? t.rows[0].cells.length : 0, rows: t.rows.length,
             overflowX: getComputedStyle(t).overflowX,
             box: t.clientWidth, content: t.scrollWidth,
             dragsInside: t.scrollWidth > t.clientWidth + 1,
             pageOverflow: Math.round(t.getBoundingClientRect().right -
                                      document.documentElement.clientWidth),
             longestWord: longestWord, longestWordText: longestWordText,
             widestCell: widestCell, widestCellText: widestCellText };
  });
  var diags = [].slice.call(md.querySelectorAll('[data-type="mermaid"]'))
    .filter(function (e) { return e.querySelector('iframe') || e.tagName === 'SECTION'; })
    .map(function (e) {
      var f = e.querySelector('iframe');
      return { box: Math.round(e.getBoundingClientRect().width),
               height: Math.round(e.getBoundingClientRect().height),
               drawnIn: f ? new URL(f.src).host : null,
               rightEdge: Math.round(e.getBoundingClientRect().right),
               sourceChars: (e.textContent || '').trim().length };
    });
  var fences = [].slice.call(md.querySelectorAll('pre')).map(function (p) {
    return { box: p.clientWidth, content: p.scrollWidth, overflowX: getComputedStyle(p).overflowX,
             clipped: p.scrollWidth > p.clientWidth + 1 && getComputedStyle(p).overflowX === 'visible' };
  });
  var real = tables.filter(function (t) { return !t.control; });
  var ctl = tables.filter(function (t) { return t.control; })[0] || null;
  return { viewport: window.innerWidth + 'x' + window.innerHeight,
           contentColumn: Math.round(md.getBoundingClientRect().width),
           documentScrollWidth: docW,
           scrollsSideways: docW > window.innerWidth + 1,
           tables: real.length, dragsInsideTables: real.filter(function (t) { return t.dragsInside; }).length,
           tablesOverflowingPage: real.filter(function (t) { return t.pageOverflow > 1; }).length,
           widestTableCellContent: real.reduce(function (a, t) { return Math.max(a, t.content); }, 0),
           longestWordInTables: real.reduce(function (a, t) { return Math.max(a, t.longestWord); }, 0),
           controlTable: ctl ? { content: ctl.content, longestWord: ctl.longestWord,
                                 pageOverflow: ctl.pageOverflow } : null,
           fences: fences.length, clippedFences: fences.filter(function (f) { return f.clipped; }).length,
           diagrams: diags.length,
           diagramsOverflowingPage: diags.filter(function (d) { return d.rightEdge > docW + 1; }).length,
           details: { tables: tables, diags: diags } };
})(${token})`;

async function main() {
  if (!urls.length) {
    console.error("usage: viewport-probe.cjs <url> [...] [--width=375] [--height=812] " +
                  "[--control [--token=N]] [--expr-file=f] [--chrome=path] [--wait=ms]");
    return 2;
  }
  const profile = fs.mkdtempSync(path.join(os.tmpdir(), "wiki-viewport-"));
  const port = 9300 + Math.floor(Math.random() * 400);
  const chrome = spawn(CHROME, ["--headless=new", "--no-sandbox", "--disable-gpu",
    `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, "about:blank"],
  { stdio: "ignore" });
  const stop = () => { try { chrome.kill("SIGKILL"); } catch { /* already gone */ } };
  process.on("exit", stop);

  let target = null;
  for (let i = 0; i < 100 && !target; i++) {
    await sleep(200);
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      target = list.find((t) => t.type === "page") || null;
    } catch { /* chrome not listening yet */ }
  }
  if (!target) { console.error(`no DevTools on port ${port}: is ${CHROME} installed?`); return 2; }

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("ws connect failed")); });
  let id = 0;
  const pending = new Map();
  let events = [];
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    else if (m.method) events.push(m.method);
  };
  const send = (method, params = {}) => new Promise((res) => {
    const n = ++id;
    pending.set(n, (m) => res(m.result === undefined ? (m.error || {}) : m.result));
    ws.send(JSON.stringify({ id: n, method, params }));
  });

  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride",
    { width, height, deviceScaleFactor: 2, mobile: true });

  const expr = exprFile ? fs.readFileSync(exprFile, "utf8") : null;
  const out = [];
  let overflow = 0;
  for (const url of urls) {
    events = [];
    await send("Page.navigate", { url });
    const t0 = Date.now();
    while (!events.includes("Page.loadEventFired") && Date.now() - t0 < 45000) await sleep(100);
    await sleep(wait);
    const expression = expr ? `(() => { return (${expr}); })()` : `(() => { return ${REPORT}; })()`;
    const r = await send("Runtime.evaluate", { expression, returnByValue: true });
    const value = r.result ? r.result.value : r;
    out.push({ url, viewport: `${width}x${height}`, result: value });
    if (value && value.scrollsSideways) overflow++;
  }
  console.log(JSON.stringify(out, null, expr ? 0 : 1));
  ws.close();
  stop();
  if (expr) return 0;
  const bad = out.filter((o) => o.result && o.result.scrollsSideways).length;
  if (bad) console.error(`${bad} page(s) scroll sideways at ${width}x${height}: a table or fence is escaping the column`);
  return bad ? 1 : 0;
}
main().catch((e) => { console.error(String(e.stack || e)); process.exit(2); });
