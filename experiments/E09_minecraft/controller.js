// E09: drives N mineflayer bots on a Paper server for one island. Python sends one JSON command per line
// over TCP and gets one JSON reply per line. Jobs are done physically (chop logs, mine stone, harvest wheat);
// walls are real blocks on a ring around the island and night mobs are real zombies the bots fight with axes.
// Usage: node controller.js --n 50 --prefix c --cx 0 --cz 0 --listen 25580
const fs = require("fs");
const net = require("net");
const mineflayer = require("mineflayer");
const Vec3 = require("vec3");
const { Rcon } = require("./rcon");
const lag = require("perf_hooks").monitorEventLoopDelay({ resolution: 20 }); lag.enable();

const arg = (k, d) => { const i = process.argv.indexOf("--" + k); return i > 0 ? process.argv[i + 1] : d; };
const N = +arg("n", 5), PREFIX = arg("prefix", "c"), CX = +arg("cx", 0), CZ = +arg("cz", 0);
const ISLAND = 15, RING = 12, MOB_R = 22;
// Flat island. Inside the ring: wheat field east, stone quarry west, log pile north, home (rest, build, night) south.
// Patches refill every 10 s while people work, so output follows effort, not patch size.
const P = { farm: [CX + 3, CX + 8, CZ - 3, CZ + 2], mine: [CX - 8, CX - 3, CZ - 3, CZ + 2], chop: [CX - 2, CX + 2, CZ - 9, CZ - 5] };
const HOME = [CX, CZ + 7];
const TARGET = { farm: new Set(["wheat"]), mine: new Set(["stone", "iron_ore", "diamond_ore"]), chop: new Set(["oak_log"]) };
const GOOD = { wheat: "food", oak_log: "wood", stone: "stone", iron_ore: "iron", diamond_ore: "diamond" };  // one dug block = one unit
const TOOL = { chop: "iron_axe", mine: "iron_pickaxe" };
const rcon = new Rcon("127.0.0.1", 25575, fs.readFileSync(process.env.HOME + "/mc/server/.rcon", "utf8").trim());
const bots = {}, dead = new Set(), errs = {}, dug = {};
let wall = [], Y = 64;
process.on("unhandledRejection", e => { errs["unhandled:" + String(e && e.message || e).slice(0, 60)] = (errs["unhandled:" + String(e && e.message || e).slice(0, 60)] || 0) + 1; });
const sleep = ms => new Promise(r => setTimeout(r, ms));
const timeout = (p, ms) => Promise.race([p, sleep(ms).then(() => { throw new Error("timeout"); })]);
const live = () => Object.keys(bots).filter(n => !dead.has(n));
const box = ([x0, x1, z0, z1], y0, y1, what) => rcon.cmd(`fill ${x0} ${y0} ${z0} ${x1} ${y1} ${z1} ${what}`);

let quitting = false;
const MOVES = new Set(["position", "position_look", "look"]);
function guardMoves(b) {  // Paper kicks on any NaN in a move packet; drop such packets and restore the last good state
  const write = b._client.write.bind(b._client);
  let good = null;
  b._client.write = (name, p) => {
    if (MOVES.has(name)) {
      const bad = ["x", "y", "z", "yaw", "pitch"].filter(k => k in p && !Number.isFinite(p[k]));
      if (bad.length) {
        errs["nan:" + bad.join()] = (errs["nan:" + bad.join()] || 0) + 1;
        if (good && b.entity) { b.entity.position.set(good.x, good.y, good.z); b.entity.velocity.set(0, 0, 0); b.entity.yaw = good.yaw; b.entity.pitch = good.pitch; }
        return;
      }
      if (b.entity) good = { x: b.entity.position.x, y: b.entity.position.y, z: b.entity.position.z, yaw: b.entity.yaw, pitch: b.entity.pitch };
    }
    return write(name, p);
  };
}
function spawnBot(name) {  // resolves once the bot stands in loaded chunks; a drop that is not a death reconnects
  return new Promise((res, rej) => {
    const b = mineflayer.createBot({ host: "localhost", port: 25565, username: name, viewDistance: "tiny", checkTimeoutInterval: 90000 });
    guardMoves(b);
    b.once("spawn", async () => {
      await timeout(b.waitForChunksToLoad(), 15000).catch(() => {});
      bots[name] = b; res(b);
    });
    b.on("death", () => dead.add(name));
    b.on("error", e => { errs["conn:" + e.message] = (errs["conn:" + e.message] || 0) + 1; rej(e); });
    b.on("end", () => {
      if (quitting || dead.has(name) || bots[name] !== b) return;
      errs.reconnect = (errs.reconnect || 0) + 1;
      setTimeout(() => spawnBot(name).catch(() => {}), 2000);
    });
  });
}

function refill() {  // solid blocks go back only in columns no bot stands in, so nobody is buried
  box(P.farm, Y, Y, "farmland");  // wheat pops off grass or dirt; same-state fills are no-ops
  box(P.farm, Y + 1, Y + 1, "wheat[age=7] replace air");
  const at = live().map(n => bots[n].entity).filter(Boolean).map(e => e.position);
  const free = (x, z) => at.every(p => Math.hypot(p.x - x - 0.5, p.z - z - 0.5) > 2);  // RCON lags; keep a margin
  for (const [job, what] of [["mine", "stone"], ["chop", "oak_log"]]) {
    const [x0, x1, z0, z1] = P[job];
    for (let x = x0; x <= x1; x++) for (let z = z0; z <= z1; z++)
      if (free(x, z)) rcon.cmd(`fill ${x} ${Y + 1} ${z} ${x} ${Y + 2} ${z} ${what} replace air`);
  }
}

async function walk(b, x, z, r, ms) {  // the island is flat: steer straight at (x, z), hop small steps, give up at the deadline
  const end = Date.now() + ms, tgt = new Vec3(x + 0.5, Y + 1, z + 0.5);
  try {
    while (Date.now() < end && b.entity && !dead.has(b.username)) {
      const p = b.entity.position;
      if (Math.hypot(p.x - tgt.x, p.z - tgt.z) <= r) return true;
      await b.lookAt(new Vec3(tgt.x, p.y + 1.6, tgt.z), true);
      b.setControlState("forward", true); b.setControlState("sprint", true);
      b.setControlState("jump", !!b.entity.isCollidedHorizontally);
      await sleep(150);
    }
    return false;
  } finally { b.clearControlStates(); }
}

function stand(job, i) {  // a spot on the patch's south edge (the side facing home), spread by bot index
  const [x0, x1, , z1] = P[job];
  return new Vec3(x0 + (i % (x1 - x0 + 1)), Y + 1, z1 + 1);
}

async function work(name, job, until, i) {  // dig the job's blocks within reach; step into dug-out space when none are left
  let b = null;
  while (TARGET[job] && Date.now() < until && !dead.has(name)) {
    if (!bots[name] || !bots[name].entity || !bots[name]._client.socket.writable) { await sleep(1000); continue; }
    if (b !== bots[name]) {  // first pass, or the bot reconnected: re-equip and go back to the patch
      b = bots[name];
      if (TOOL[job]) { const it = b.inventory.items().find(t => t.name === TOOL[job]); if (it) await b.equip(it, "hand").catch(() => {}); }
      const s = stand(job, i);
      if (!await walk(b, s.x, s.z, 0.8, 15000)) errs.stand_late = (errs.stand_late || 0) + 1;
    }
    try {
      const eye = b.entity.position.offset(0, 1.6, 0);
      const near = b.findBlocks({ point: b.entity.position, matching: x => TARGET[job].has(x.name), maxDistance: 5, count: 8 })
        .filter(p => p.offset(0.5, 0.5, 0.5).distanceTo(eye) < 4.4);
      if (!near.length) {  // nothing in reach: walk next to the nearest target, through space already dug
        const far = b.findBlock({ point: b.entity.position, matching: x => TARGET[job].has(x.name), maxDistance: 12 });
        if (!far) { await sleep(700); continue; }
        if (!await walk(b, far.position.x, far.position.z, 2.5, 3000)) errs.walk_late = (errs.walk_late || 0) + 1;
        await sleep(200); continue;
      }
      const blk = b.blockAt(near[0]);
      await timeout(b.dig(blk, true), 6000);
      const g = GOOD[blk.name]; dug[name][g] = (dug[name][g] || 0) + 1;
    } catch (e) { errs["dig:" + e.message] = (errs["dig:" + e.message] || 0) + 1; await sleep(300); }
  }
  if (bots[name] && bots[name].entity) await walk(bots[name], HOME[0], HOME[1], 3, 15000);
}

function ringFree(k) {  // the next k free columns of the wall ring
  const have = new Set(wall.map(p => p.join())), out = [];
  const steps = Math.ceil(2 * Math.PI * RING * 1.5);
  for (let i = 0; i < steps && out.length < k; i++) {
    const a = 2 * Math.PI * i / steps, x = Math.round(CX + RING * Math.cos(a)), z = Math.round(CZ + RING * Math.sin(a));
    const key = [x, z].join();
    if (!have.has(key)) { have.add(key); out.push([x, z]); }
  }
  return out;
}

async function defend(b, until) {  // night: hit the nearest zombie in reach with the axe
  while (Date.now() < until && !dead.has(b.username)) {
    const z = b.nearestEntity(e => e.name === "zombie" && e.position.distanceTo(b.entity.position) < 3.5);
    if (z) { await b.lookAt(z.position.offset(0, 1.5, 0)).catch(() => {}); b.attack(z); }
    await sleep(650);
  }
}

const cmds = {
  async setup() {
    for (const r of ["doDaylightCycle false", "doMobSpawning false", "naturalRegeneration false", "doWeatherCycle false",
      "announceAdvancements false"]) await rcon.cmd("gamerule " + r);
    await rcon.cmd(`forceload add ${CX - 32} ${CZ - 32} ${CX + 32} ${CZ + 32}`);
    await rcon.cmd("time set day"); await sleep(2000);
    Y = 100;  // flat island at y=100 over whatever is below, 31x31, clear air above
    const sq = [CX - ISLAND, CX + ISLAND, CZ - ISLAND, CZ + ISLAND];
    await box(sq, Y + 1, Y + 8, "air"); await box(sq, Y - 2, Y - 1, "dirt"); await box(sq, Y, Y, "grass_block");
    await box([CX - MOB_R - 3, CX + MOB_R + 3, CZ - MOB_R - 3, CZ - ISLAND - 1], Y, Y, "grass_block");  // mob ground, 4 sides
    await box([CX - MOB_R - 3, CX + MOB_R + 3, CZ + ISLAND + 1, CZ + MOB_R + 3], Y, Y, "grass_block");
    await box([CX - MOB_R - 3, CX - ISLAND - 1, CZ - ISLAND, CZ + ISLAND], Y, Y, "grass_block");
    await box([CX + ISLAND + 1, CX + MOB_R + 3, CZ - ISLAND, CZ + ISLAND], Y, Y, "grass_block");
    wall = []; refill();
    await rcon.cmd(`setworldspawn ${HOME[0]} ${Y + 1} ${HOME[1]}`); await rcon.cmd("gamerule spawnRadius 2");
    const pd = process.env.HOME + "/mc/server/world/playerdata";  // saved positions from past runs would override the world spawn
    for (const f of fs.readdirSync(pd)) fs.rmSync(pd + "/" + f, { force: true });
    for (let i = 0; i < N; i++) { await spawnBot(PREFIX + i).catch(() => {}); await sleep(1000); }
    for (const n of live()) await rcon.cmd(`tp ${n} ${HOME[0] + Math.floor(Math.random() * 7) - 3}.5 ${Y + 1} ${HOME[1] + Math.floor(Math.random() * 5) - 2}.5`);
    await sleep(2000);
    return { bots: live().length, y: Y };
  },
  async day({ assign, work_s = 45 }) {
    refill();
    const miners = Object.values(assign).filter(j => j === "mine").length;  // ore: about 40% / 5% per mine-day
    for (let i = 0; i < miners; i++) for (const [ore, p] of [["iron_ore", 0.4], ["diamond_ore", 0.05]]) if (Math.random() < p) {
      const [x0, , z0] = P.mine;
      await rcon.cmd(`setblock ${x0 + Math.floor(Math.random() * 6)} ${Y + 1 + Math.floor(Math.random() * 2)} ${z0 + Math.floor(Math.random() * 6)} ${ore}`);
    }
    const who = Object.keys(assign).filter(n => bots[n] && !dead.has(n));
    for (const n of who) { await rcon.cmd(`clear ${n}`); await rcon.cmd(`give ${n} iron_axe`); await rcon.cmd(`give ${n} iron_pickaxe`); }
    await rcon.cmd(`effect give @a resistance ${work_s + 30} 4 true`);  // daytime only: no deaths from a refill landing on a worker
    await sleep(800);
    for (const n of who) dug[n] = {};
    const mspt = [];
    const until = Date.now() + work_s * 1000, regrow = setInterval(() => {
      refill(); rcon.cmd(`kill @e[type=item,x=${CX},y=${Y},z=${CZ},distance=..40]`).catch(() => {});
      rcon.cmd("mspt").then(r => mspt.push(r.replace(/\u00a7./g, "").replace(/\s+/g, " ").trim().slice(0, 120))).catch(() => {});
    }, 5000);
    const idx = {};  // spread bots on the same job across stand points
    await Promise.all(who.map(n => { const j = assign[n]; idx[j] = (idx[j] || 0) + 1; return work(n, j, until, idx[j] - 1); }));
    clearInterval(regrow);
    const gained = Object.fromEntries(who.map(n => [n, dug[n] || {}]));
    const e = { ...errs, mspt, lag_p99_ms: Math.round(lag.percentile(99) / 1e6), lag_max_ms: Math.round(lag.max / 1e6) }; lag.reset(); for (const k in errs) delete errs[k];
    return { errors: e, gained, alive: live() };
  },
  async night({ zombies = 0, night_s = 45, wall_target = 0 }) {  // the caller owns the wall count; decay happens there
    await rcon.cmd("effect clear @a resistance"); await rcon.cmd("time set midnight");
    while (wall.length > wall_target) { const [x, z] = wall.pop(); await rcon.cmd(`fill ${x} ${Y + 1} ${z} ${x} ${Y + 2} ${z} air`); }
    for (const [x, z] of ringFree(wall_target - wall.length)) {  // one contiguous arc, filled in angle order
      await rcon.cmd(`fill ${x} ${Y + 1} ${z} ${x} ${Y + 2} ${z} cobblestone`); wall.push([x, z]);
    }
    await Promise.all(live().map(n => walk(bots[n], HOME[0], HOME[1], 4, 15000)));
    for (let i = 0; i < zombies; i++) {  // evenly round the island, outside the ring
      const a = 2 * Math.PI * i / Math.max(1, zombies);
      await rcon.cmd(`summon zombie ${Math.round(CX + MOB_R * Math.cos(a))} ${Y + 1} ${Math.round(CZ + MOB_R * Math.sin(a))} {PersistenceRequired:1b}`);
    }
    const before = new Set(dead), until = Date.now() + night_s * 1000;
    await Promise.all(live().map(n => defend(bots[n], until)));
    await rcon.cmd(`kill @e[type=zombie,x=${CX},y=${Y},z=${CZ},distance=..60]`);
    await rcon.cmd(`kill @e[type=item,x=${CX},y=${Y},z=${CZ},distance=..60]`);
    await rcon.cmd("time set day");
    for (const n of live()) await rcon.cmd(`effect give ${n} instant_health 1 5`);
    const died = [...dead].filter(n => !before.has(n));
    for (const n of died) bots[n].quit();  // hardcore: out for good
    return { died, wall: wall.length, alive: live() };
  },
  ring() { return { ring: ringFree(1e4).length + wall.length }; },
  async kill({ names }) { for (const n of names) if (bots[n] && !dead.has(n)) { dead.add(n); await rcon.cmd(`kill ${n}`); bots[n].quit(); } return {}; },
  async quit() { quitting = true; for (const b of Object.values(bots)) b.quit(); setTimeout(() => process.exit(0), 500); return {}; },
};

net.createServer(sock => {
  let buf = "", chain = Promise.resolve();
  sock.on("data", d => {
    buf += d; let i;
    while ((i = buf.indexOf("\n")) >= 0) {
      const msg = JSON.parse(buf.slice(0, i)); buf = buf.slice(i + 1);
      chain = chain.then(async () => {  // one command at a time, replies in order
        try { sock.write(JSON.stringify({ ok: true, ...(await cmds[msg.cmd](msg)) }) + "\n"); }
        catch (e) { sock.write(JSON.stringify({ ok: false, error: String(e) }) + "\n"); }
      });
    }
  });
}).listen(+arg("listen", 25580), "0.0.0.0", () => console.log("listening"));
