// Smoke test: N bots (--n, default 8) on a fixed job cycle, one day, one night with N*3/4 zombies.
const net = require("net");
const n = +(process.argv[process.argv.indexOf("--n") + 1] || 8);
const s = net.connect(25580, "127.0.0.1"); let buf = "", wait = [];
s.on("data", d => { buf += d; let i; while ((i = buf.indexOf("\n")) >= 0) { wait.shift()(JSON.parse(buf.slice(0, i))); buf = buf.slice(i + 1); } });
const call = m => new Promise(r => { wait.push(r); s.write(JSON.stringify(m) + "\n"); });
const JOBS = ["chop", "mine", "farm", "build_wall", "rest", "farm", "mine", "chop"];
(async () => {
  let t = Date.now();
  console.log("setup", JSON.stringify(await call({ cmd: "setup" })), (Date.now() - t) / 1000 + "s");
  const assign = Object.fromEntries([...Array(n)].map((_, i) => ["c" + i, JOBS[i % JOBS.length]]));
  t = Date.now(); const d = await call({ cmd: "day", assign, work_s: 45 });
  const tot = {}; for (const g of Object.values(d.gained)) for (const [k, v] of Object.entries(g)) tot[k] = (tot[k] || 0) + v;
  const idle = Object.entries(d.gained).filter(([b, g]) => !Object.keys(g).length && ["chop", "mine", "farm"].includes(assign[b])).map(([b]) => b);
  console.log("day", JSON.stringify({ errors: d.errors, total: tot, idle_workers: idle, alive: d.alive.length }), (Date.now() - t) / 1000 + "s");
  t = Date.now(); const nt = await call({ cmd: "night", zombies: Math.round(n * 3 / 4), night_s: 40, wall_target: 30 });
  console.log("night", JSON.stringify({ died: nt.died.length, wall: nt.wall, alive: nt.alive.length }), (Date.now() - t) / 1000 + "s");
  await call({ cmd: "quit" }); process.exit(0);
})();
