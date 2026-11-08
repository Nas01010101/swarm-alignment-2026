// Debug: one bot, print RCON replies for the island fills and what the bot sees at the patches.
const mineflayer = require("mineflayer"); const Vec3 = require("vec3"); const { Rcon } = require("./rcon");
const rcon = new Rcon("127.0.0.1", 25575, require("fs").readFileSync(process.env.HOME + "/mc/server/.rcon", "utf8").trim());
(async () => {
  console.log("forceload", await rcon.cmd("forceload add -32 -32 32 32"));
  console.log("fill", await rcon.cmd("fill 3 101 -3 8 101 2 wheat[age=7] replace air"));
  console.log("fill2", await rcon.cmd("fill -8 101 -3 -3 102 2 stone replace air"));
  const b = mineflayer.createBot({ host: "localhost", port: 25565, username: "Dbg" });
  b.once("spawn", async () => {
    console.log("tp", await rcon.cmd("tp Dbg 0 101 7")); await new Promise(r => setTimeout(r, 3000));
    console.log("pos", b.entity.position, "game", b.game.gameMode);
    for (const p of [[5, 101, 0], [5, 100, 0], [-5, 101, 0], [0, 100, 7]]) { const k = b.blockAt(new Vec3(...p)); console.log(p, k && k.name); }
    const f = b.findBlock({ point: new Vec3(5, 101, 0), matching: x => x.name === "wheat", maxDistance: 6 });
    console.log("find wheat", f && f.position);
    const g = b.findBlock({ matching: x => x.name === "stone", maxDistance: 16 });
    console.log("find stone", g && g.position, "ids", b.registry.blocksByName.wheat.id);
    b.quit(); process.exit(0);
  });
})();
