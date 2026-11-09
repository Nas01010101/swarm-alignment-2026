// Spectator camera: one bot in spectator mode, prismarine-viewer + headless Chrome for screenshots.
const fs = require("fs"), mineflayer = require("mineflayer"), { mineflayer: viewer } = require("prismarine-viewer");
const puppeteer = require("puppeteer");
const { Rcon } = require(process.env.HOME + "/mc/bots/rcon");
const rcon = new Rcon("127.0.0.1", 25575, fs.readFileSync(process.env.HOME + "/mc/server/.rcon", "utf8").trim());
const sleep = ms => new Promise(r => setTimeout(r, ms));
const OUT = process.env.HOME + "/mc/shots"; fs.mkdirSync(OUT, { recursive: true });
const ROUNDS = +(process.argv[2] || 6), GAP = +(process.argv[3] || 60) * 1000;
// [label, x, y, z, yaw, pitch]  minecraft yaw 0 = facing +z
const VIEWS = [["A_over", 0, 128, -26, 0, 45], ["B_over", 300, 128, -26, 0, 45],
               ["A_low", -14, 104, -14, -45, 15], ["B_low", 286, 104, -14, -45, 15]];
const bot = mineflayer.createBot({ host: "127.0.0.1", port: 25565, username: "cam", version: "1.21.4" });
bot.once("spawn", async () => {
  bot.physicsEnabled = false; await rcon.cmd("gamemode spectator cam");
  viewer(bot, { port: 3007, firstPerson: true, viewDistance: 4 });
  const br = await puppeteer.launch({ headless: true, args: ["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
  const pg = await br.newPage(); await pg.setViewport({ width: 1280, height: 720 });
  await pg.goto("http://127.0.0.1:3007"); await sleep(3000);
  for (let r = 0; r < ROUNDS; r++) {
    const t = (await rcon.cmd("time query daytime")).replace(/\D/g, ""), phase = +t >= 13000 ? "night" : "day";
    for (const [lab, x, y, z, yaw, pitch] of VIEWS) {
      await rcon.cmd(`tp cam ${x} ${y} ${z} ${yaw} ${pitch}`); await sleep(1500); bot.entity.position.set(x, y, z); await bot.look((180 - yaw) * Math.PI / 180, -pitch * Math.PI / 180, true); await sleep(8000);
      const near = Object.values(bot.entities).filter(e => e !== bot.entity && e.position.distanceTo(bot.entity.position) < 60);
      const f = `${OUT}/${new Date().toISOString().slice(11, 19).replace(/:/g, "")}_${lab}_${phase}.png`;
      await pg.screenshot({ path: f });
      console.log(f, "players", near.filter(e => e.type === "player").length, "zombies", near.filter(e => e.name === "zombie").length);
    }
    await sleep(GAP);
  }
  await br.close(); bot.quit(); process.exit(0);
});
bot.on("error", e => console.log("err", e.message)); bot.on("kicked", k => console.log("kicked", k));
