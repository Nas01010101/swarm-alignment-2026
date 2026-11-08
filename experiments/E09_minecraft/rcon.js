// Minimal Source RCON client (Minecraft): auth once, then one command at a time.
const net = require("net");
class Rcon {
  constructor(host, port, pw) { this.host = host; this.port = port; this.pw = pw; this.id = 0; this.q = Promise.resolve(); }
  _send(type, body) {
    return new Promise((res, rej) => {
      const id = ++this.id, b = Buffer.from(body, "utf8"), p = Buffer.alloc(14 + b.length);
      p.writeInt32LE(10 + b.length, 0); p.writeInt32LE(id, 4); p.writeInt32LE(type, 8); b.copy(p, 12);
      let buf = Buffer.alloc(0);
      const on = d => { buf = Buffer.concat([buf, d]);
        while (buf.length >= 4 && buf.length >= 4 + buf.readInt32LE(0)) {
          const len = buf.readInt32LE(0), rid = buf.readInt32LE(4), txt = buf.toString("utf8", 12, 4 + len - 2);
          buf = buf.slice(4 + len);
          if (rid === -1) { this.s.off("data", on); return rej(new Error("rcon auth failed")); }
          if (rid === id) { this.s.off("data", on); return res(txt); }
        } };
      this.s.on("data", on); this.s.write(p);
    });
  }
  async connect() {
    this.s = net.connect(this.port, this.host); await new Promise((r, j) => { this.s.once("connect", r); this.s.once("error", j); });
    await this._send(3, this.pw);
  }
  cmd(c) {  // serialised: RCON replies are matched by id, one in flight at a time
    const p = this.q.then(async () => { if (!this.s) await this.connect(); return this._send(2, c); });
    this.q = p.catch(() => {});  // one failed command must not block the rest
    return p;
  }
}
module.exports = { Rcon };
