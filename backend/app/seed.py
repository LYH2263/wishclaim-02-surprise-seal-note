from app.db import connect

def init_db():
    c = connect()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS wishes(
      id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, note TEXT, status TEXT,
      claimer TEXT, claimed_at TEXT, expires_at TEXT, seal_note INTEGER NOT NULL DEFAULT 0,
      data_quality TEXT
    );
    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
    """)
    cols = {r["name"] for r in c.execute("PRAGMA table_info(wishes)")}
    if "seal_note" not in cols:
        c.execute("ALTER TABLE wishes ADD COLUMN seal_note INTEGER NOT NULL DEFAULT 0")
    if c.execute("SELECT COUNT(*) c FROM wishes").fetchone()["c"] == 0:
        c.executemany(
            "INSERT INTO wishes(title,note,status,claimer,claimed_at,expires_at,seal_note,data_quality)"
            " VALUES (?,?,?,?,?,?,?,?)",
            [
                ("机械键盘", "红轴", "open", None, None, None, 0, "clean"),
                ("围巾", "羊毛", "open", None, None, None, 0, "clean"),
                ("脏愿望-空标题", "", "open", None, None, None, 0, "dirty"),
                ("过期锁样例", "应被TTL释放", "claimed", "ghost", "2020-01-01T00:00:00+00:00",
                 "2020-01-01T01:00:00+00:00", 0, "dirty"),
                ("神秘礼物", "核销后揭晓的悄悄话", "open", None, None, None, 1, "clean"),
                ("封存祝福(已核销)", "谢谢你，这一年的照顾", "fulfilled", "访客", None, None, 1, "clean"),
            ],
        )
        c.execute("INSERT INTO settings(key,value) VALUES ('ttl_seconds','86400')")
        c.execute("INSERT INTO settings(key,value) VALUES ('wall_title','暖粉愿望墙')")
        c.commit()
    c.close()
