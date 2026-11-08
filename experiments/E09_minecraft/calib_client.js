// E09 calibration (prereg): blocks dug per job-day at 50 bots, and zombie deaths at zero wall for several counts.
// Usage: node calib_client.js --n 50 --zombies 25,50,100   (zombie sweep, no wall)
//        node calib_client.js --n 50 --zombies 50 --walls 0,19,38,57,76   (wall sweep)
const net = require("net");
const arg = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
const n = +arg("n", 50), Z = arg("zombies", "25,50,100").split(",").map(Number);
const W = arg("walls", "0").split(",").map(Number);
const nights = W.length > 1 ? W.map(w => [Z[0], w]) : Z.map(z => [z, W[0]]);
const s = net.connect(25580, "127.0.0.1"); let buf = "", wait = [];
s.on("data", d => { buf += d; let i; while ((i = buf.indexOf("\n")) >= 0) { wait.shift()(JSON.parse(buf.slice(0, i))); buf = buf.slice(i + 1); } });
const call = m => new Promise(r => { wait.push(r); s.write(JSON.stringify(m) + "\n"); });
const JOBS = ["chop", "mine", "farm", "build_wall", "rest", "farm", "mine", "chop"];
(async () => {
  console.log(JSON.stringify({ setup: await call({ cmd: "setup" }) }));
  const assign = Object.fromEntries([...Array(n)].map((_, i) => ["c" + i, JOBS[i % JOBS.length]]));
  const d = await call({ cmd: "day", assign, work_s: 45 });
  const per = {};  // blocks per worker by job
  for (const [b, g] of Object.entries(d.gained)) { const j = assign[b]; per[j] = per[j] || []; per[j].push(g); }
  console.log(JSON.stringify({ day: { errors: d.errors, per_job: per } }));
  for (const [z, w] of nights) {
    const nt = await call({ cmd: "night", zombies: z, night_s: 45, wall_target: w });
    console.log(JSON.stringify({ night: { zombies: z, wall: nt.wall, alive_before: nt.alive.length + nt.died.length, died: nt.died.length } }));
  }
  await call({ cmd: "quit" }); process.exit(0);
})();
