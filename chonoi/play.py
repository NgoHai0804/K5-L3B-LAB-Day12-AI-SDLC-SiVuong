"""Chơi trọn mùa nước nổi trên trình duyệt: chạy ĐÚNG `DaySim` (mode day) của headless, 5 Ngày theo kế hoạch.

    python3 -m chonoi.play [--seed N] [--port 8000] [--save-dir saves]

Màn: Menu (Chơi / Thoát) -> DayIntro (Má Tư đọc danh sách, tự chuyển sau 4 s) -> Sáng lặn -> EveningIntro
-> Tối mở quán -> DayResult -> Shop -> Ngày kế ... -> Tổng kết. Esc/P tạm dừng (pause của sim: dừng mọi timer).

Sáng tạo của nhóm (CHỈ ở cửa sổ chơi; headless KHÔNG đổi, vẫn đọc nguyên game.contract.json):
  - cốt truyện Má Tư / Út Sen, mục tiêu tiền thuốc, kết thúc theo kết quả;
  - sprint (giữ Shift): bơi ×1.5, oxy ×1.5, có thanh thể lực;
  - đồ nghề thêm ở Shop (giỏ, chân vịt, vợt, bếp, ghế): đổi một BẢN SAO tuning từ Ngày kế, vẫn qua validate_tuning;
  - lưu tiến trình ở ranh giới Ngày vào `<save-dir>/campaign.json`.

API thêm (ngoài /state, /input của live):
    POST /next   -> qua màn hiện tại (menu -> intro -> chơi ...; ở Shop = đóng Shop)
    POST /new    -> chơi mới từ Ngày 1
    POST /buy    -> {"id": "oxygen" | "hp" | <đồ nghề>}
    POST /menu   -> về menu chính (bỏ phần dở của Ngày đang chơi)
    POST /quit   -> thoát game (tắt máy chủ)
"""

import argparse
import copy
import json
import os
import random
import sys
import threading
import time
from http.server import ThreadingHTTPServer

from .contract import load_contract, validate_tuning
from .errors import BadInput
from .live import RECENT_EVENTS, LiveGame, _Handler
from .runner import Session

MAX_DAYS = 5
GOAL = 1500  # nghìn đồng: tiền thuốc + sửa nhà bè cho Má Tư
INTRO_TICKS = 240  # DayIntro tự chuyển sau 4 s
PLAY_STAGES = ("gather", "quan", "shop")

# đồ nghề sáng tạo: id -> (tên, mô tả, giá theo cấp)
GEAR = {
    "gio": ("Giỏ lưới rộng", "+4 ô trong giỏ", [120, 260]),
    "chan": ("Chân vịt tre", "+0.5 m/s tốc độ bơi", [150, 300]),
    "vot": ("Vợt cán dài", "+0.5 m tầm hái và bắt", [100, 220]),
    "bep": ("Bếp lò mới", "nấu nhanh hơn 20%", [180, 360]),
    "ghe": ("Ghế đẩu êm", "+10 giây kiên nhẫn của khách", [150, 300]),
}
CORE_NAMES = {"oxygen": ("Bình oxy", "oxy tối đa"), "hp": ("Áo phao", "thêm Máu")}

# Món phụ của quán (sáng tạo): ít nguyên liệu, nấu nhanh, giá rẻ -> khách gọi đa dạng hơn.
EXTRA_DISHES = {
    "ca_linh_chien": {"recipe": {"ca_linh": 1}, "cook_s": 3, "price": 30},
    "bong_sung_xao": {"recipe": {"bong_sung": 1}, "cook_s": 3, "price": 25},
    "dien_dien_xao_trung": {"recipe": {"bong_dien_dien": 1}, "cook_s": 3, "price": 30},
    "keo_neo_luoc": {"recipe": {"keo_neo": 1}, "cook_s": 3, "price": 25},
    "chao_ca_loc": {"recipe": {"ca_loc": 1}, "cook_s": 5, "price": 45},
    "ca_keo_kho": {"recipe": {"ca_keo": 1}, "cook_s": 5, "price": 40},
}
KIND_NAME = {"ca_loc": "cá lóc", "ca_linh": "cá linh", "ca_keo": "cá kèo", "bong_dien_dien": "bông điên điển",
             "bong_sung": "bông súng", "keo_neo": "kèo nèo"}
DISH_NAME = {"ca_loc_nuong_trui": "cá lóc nướng trui", "goi_bong_sung": "gỏi bông súng",
             "lau_ca_linh_dien_dien": "lẩu cá linh", "canh_chua_ca_loc": "canh chua cá lóc",
             "ca_keo_nuong": "cá kèo nướng", "lau_mam": "lẩu mắm"}


def make_quests(seed, day, plan):
    """3 nhiệm vụ phụ ngẫu nhiên (tất định theo seed + Ngày), có thưởng tiền khi xong."""
    rng = random.Random(f"{seed}:quest:{day}")
    pool = []
    for k in ("ca_linh", "ca_loc", "ca_keo"):
        n = rng.choice((2, 3))
        pool.append({"type": "catch", "kind": k, "n": n, "reward": 25 + 10 * n, "text": f"Bắt {n} đàn {KIND_NAME[k]}"})
    for k in ("bong_dien_dien", "bong_sung", "keo_neo"):
        n = rng.choice((2, 3, 4))
        pool.append({"type": "gather", "kind": k, "n": n, "reward": 15 + 8 * n, "text": f"Hái {n} {KIND_NAME[k]}"})
    n = rng.choice((3, 4, 5))
    pool.append({"type": "serve", "n": n, "reward": 10 * n + 20, "text": f"Phục vụ {n} khách"})
    n = rng.choice((2, 3))
    pool.append({"type": "tips", "n": n, "reward": 20 * n, "text": f"Được {n} khách boa"})
    pool.append({"type": "deep", "n": 25, "reward": 40, "text": "Lặn xuống sâu 25 m"})
    pool.append({"type": "no_hit", "reward": 50, "text": "Không bị Cá Sấu đớp", "end": "gather"})
    pool.append({"type": "no_left", "reward": 60, "text": "Không để khách nào bỏ về", "end": "quan"})
    pool.append({"type": "fresh", "n": 2, "reward": 45, "text": "Nấu 2 món nguyên liệu tươi rói (≥ 95%)"})
    dish = rng.choice(sorted(plan["dishes"]))
    pool.append({"type": "dish", "dish": dish, "n": 1, "reward": 35, "text": f"Bán được 1 {DISH_NAME.get(dish, dish)}"})
    picked = rng.sample(pool, 3)
    for i, q in enumerate(picked):
        q.update(id=f"Q{i + 1}", done=False, failed=False, progress=0)
    return picked


_TUNING_CACHE = {}


def day_tuning(base, day, gear):
    """Tuning của Ngày `day` với đồ nghề `gear` + món phụ (bản sao; phần lõi vẫn qua validate_tuning)."""
    key = (id(base), tuple(sorted(gear.items())))
    if key not in _TUNING_CACHE:
        _TUNING_CACHE[key] = _make_tuning(base, gear)
    return _TUNING_CACHE[key]


def _make_tuning(base, gear):
    t = copy.deepcopy(base)
    g, q = t["gather"], t["quan"]
    g["hold_capacity"] += 4 * gear.get("gio", 0)
    g["swim_speed"] += 0.5 * gear.get("chan", 0)
    g["catch_radius"] += 0.5 * gear.get("vot", 0)
    g["interact_radius"] += 0.5 * gear.get("vot", 0)
    for d in t["menu"].values():
        d["cook_s"] = round(d["cook_s"] * (1 - 0.2 * gear.get("bep", 0)), 2)
    q["patience_s"] = q["patience_s"] + 10 * gear.get("ghe", 0)
    validate_tuning(t)
    for k, d in EXTRA_DISHES.items():  # món phụ thêm SAU khi kiểm (contract lõi cố định đúng 6 món)
        t["menu"][k] = dict(d, cook_s=round(d["cook_s"] * (1 - 0.2 * gear.get("bep", 0)), 2))
    return t


class CampaignGame(LiveGame):
    EXTRAS = dict(LiveGame.EXTRAS, extra_dishes=tuple(EXTRA_DISHES))

    def __init__(self, tuning, seed, save_dir):
        self.base_tuning = tuning
        self.base_seed = seed
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        self.save_file = os.path.join(save_dir, "campaign.json")
        self.quit_requested = threading.Event()
        self._fresh_state()
        self.saved = self._load()
        super().__init__("day", tuning, {}, seed)
        self.stage = "title"

    # --- trạng thái giữa các Ngày -------------------------------------------------------------
    def _fresh_state(self):
        self.start_day = 1
        self.day_start_state = {"money": 0, "earned": 0, "reputation": self.base_tuning["quan"]["reputation_initial"],
                      "upgrades": {}}
        self.gear = {k: 0 for k in GEAR}
        self.history = []
        self.today = {}
        self.stage = "title"
        self.intro_ticks = 0

    def _load(self):
        try:
            with open(self.save_file, encoding="utf-8") as f:
                d = json.load(f)
            if not (1 <= int(d["day"]) <= MAX_DAYS) or d.get("finished"):
                return None
            return d
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _save(self, finished=False):
        sim = self.session.sim
        d = {"day": sim.day if not finished else MAX_DAYS, "finished": finished,
             "money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
             "upgrades": dict(sim.upgrades), "gear": self.gear, "history": self.history, "seed": self.base_seed}
        tmp = self.save_file + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False)
            os.replace(tmp, self.save_file)
        except OSError as e:
            sys.stderr.write(f"không lưu được tiến trình: {e}\n")

    def _reset(self):
        """Dựng phiên `day` bắt đầu ở `self.start_day` với trạng thái `self.day_start_state`."""
        scen = {"day": {"money": self.day_start_state["money"], "earned": self.day_start_state["earned"],
                        "reputation": self.day_start_state["reputation"], "upgrades": dict(self.day_start_state["upgrades"])}}
        gear = self.gear
        self.session = Session("day", self.base_tuning, scen, self.base_seed, days=MAX_DAYS, extras=self.EXTRAS,
                               day_tuning=lambda day, active: day_tuning(self.base_tuning, day, gear),
                               start_day=self.start_day)
        from .inputs import LiveInputs
        self.inputs = LiveInputs()
        self.events = []
        self.error = None
        self._saved = False
        self.session.initial_events()
        self.today = self._new_today()
        self.intro_ticks = 0

    def _new_today(self):
        sim = self.session.sim
        return {"day": sim.day, "money0": sim.money, "earned0": sim.earned, "rep0": sim.reputation,
                "fish_caught": 0, "gather": 0, "served": 0, "left": 0, "no_dish": 0, "tips": 0, "choke": 0,
                "monster_hit": 0, "spoiled": 0, "dishes": {}, "inventory": [], "caught": {}, "picked": {},
                "tip_count": 0, "max_depth": 0.0, "fresh_cooks": 0, "quest_reward": 0,
                "quests": make_quests(self.base_seed, sim.day, sim.plan_today())}

    def _snapshot_start(self):
        sim = self.session.sim
        self.start_day = sim.day
        self.day_start_state = {"money": sim.money, "earned": sim.earned, "reputation": sim.reputation,
                      "upgrades": dict(sim.upgrades)}

    # --- vòng tick -------------------------------------------------------------------------------
    def _tick_once(self):
        if self.stage == "dayintro":
            self.intro_ticks += 1
            if self.intro_ticks >= INTRO_TICKS:
                self.stage = "gather"
            return
        if self.stage not in PLAY_STAGES or self.session.done:
            return
        rows = self.session.step(self.inputs.advance())
        self.events.extend(rows)
        del self.events[:-RECENT_EVENTS]
        td = self.today
        sub = self.session.sim.sub
        if sub.phase == "gather":
            td["max_depth"] = max(td["max_depth"], sub.pos[1])
        for r in rows:
            n, d = r["name"], r["data"]
            if n in ("fish_caught", "gather", "choke", "monster_hit", "spoiled", "no_dish"):
                td[n] += 1
            if n == "fish_caught":
                td["caught"][d["kind"]] = td["caught"].get(d["kind"], 0) + 1
            elif n == "gather":
                td["picked"][d["kind"]] = td["picked"].get(d["kind"], 0) + d["amount"]
            elif n == "dropped":
                td["picked"][d["kind"]] = max(0, td["picked"].get(d["kind"], 0) - 1)
            elif n == "cook_started":
                price = self.session.sim.tuning["menu"][d["dish_id"]]["price"]
                if d["base_price"] * 100 >= price * 95:
                    td["fresh_cooks"] += 1
            elif n == "served":
                td["served"] += 1
                td["dishes"][d["dish_id"]] = td["dishes"].get(d["dish_id"], 0) + 1
            elif n == "customer_left" and d["reason"] == "patience":
                td["left"] += 1
            elif n == "paid":
                td["tips"] += d["tip"]
                td["tip_count"] += 1 if d["tip"] > 0 else 0
            elif n == "gather_end":
                td["gather_reason"] = d["reason"]
                td["inventory"] = d["inventory"]["items"]
                self._quests_end("gather")
            elif n == "phase_start" and r["phase"] == "quan":
                self.stage = "eveningintro"
            elif n == "phase_start" and r["phase"] == "shop":
                self._close_day()
                self.stage = "dayresult"
            elif n == "day_start":
                self._snapshot_start()
                self.today = self._new_today()
                self.intro_ticks = 0
                self.stage = "story"
                self._save()
        if rows or sub.phase == "gather":
            self._quests_progress()
        if self.session.done:
            self.stage = "ending"
            self._save(finished=True)

    # --- nhiệm vụ phụ -------------------------------------------------------------------------------
    def _quests_progress(self):
        td = self.today
        vals = {"catch": lambda q: td["caught"].get(q.get("kind"), 0),
                "gather": lambda q: td["picked"].get(q.get("kind"), 0),
                "serve": lambda q: td["served"], "tips": lambda q: td["tip_count"],
                "deep": lambda q: int(td["max_depth"]), "fresh": lambda q: td["fresh_cooks"],
                "dish": lambda q: td["dishes"].get(q.get("dish"), 0)}
        for q in td.get("quests", []):
            if q["done"] or q["failed"]:
                continue
            t = q["type"]
            if t not in vals:
                if (t == "no_hit" and td["monster_hit"]) or (t == "no_left" and td["left"]):
                    q["failed"] = True
                continue
            q["progress"] = min(q["n"], vals[t](q))
            if q["progress"] >= q["n"]:
                q["done"] = True

    def _quests_end(self, phase):
        self._quests_progress()
        for q in self.today.get("quests", []):
            if q.get("end") == phase and not q["failed"]:
                q["done"] = True

    def _close_day(self):
        sim = self.session.sim
        td = self.today
        self._quests_end("quan")
        reward = sum(q["reward"] for q in td.get("quests", []) if q["done"])
        if reward:  # thưởng nhiệm vụ (sáng tạo): cộng vào ví và tổng thu trước khi mở Shop
            sim.money += reward
            sim.earned += reward
        td["quest_reward"] = reward
        td.update(money=sim.money - td["money0"], earned=sim.earned - td["earned0"], reputation=sim.reputation)
        self.history.append({k: td[k] for k in ("day", "money", "earned", "reputation", "served", "left", "tips",
                                                 "dishes", "quest_reward")})

    # --- chuyển màn ---------------------------------------------------------------------------------
    def next_stage(self):
        with self._lock:
            st = self.stage
            if st == "title":
                if self.saved:
                    self._resume(self.saved)
                else:
                    self._fresh_state()
                    self._reset()
                self.stage = "story"
            elif st == "story":
                self.stage = "dayintro"
            elif st == "dayintro":
                self.stage = "gather"
            elif st == "eveningintro":
                self.stage = "quan"
            elif st == "dayresult":
                self.stage = "shop"
            elif st == "shop":
                self.inputs.press("shop_done")
            elif st == "ending":
                self._fresh_state()
                self.saved = None
                self._reset()
                self.stage = "title"

    def _resume(self, d):
        self._fresh_state()
        self.start_day = int(d["day"])
        self.day_start_state = {"money": int(d.get("money", 0)), "earned": int(d.get("earned", 0)),
                      "reputation": float(d.get("reputation", self.day_start_state["reputation"])),
                      "upgrades": {k: int(v) for k, v in d.get("upgrades", {}).items() if k in CORE_NAMES}}
        self.gear.update({k: int(v) for k, v in d.get("gear", {}).items() if k in GEAR})
        self.history = list(d.get("history", []))[: self.start_day - 1]
        self.saved = None
        self._reset()

    def new_game(self):
        with self._lock:
            try:
                os.remove(self.save_file)
            except OSError:
                pass
            self._fresh_state()
            self.saved = None
            self._reset()
            self.stage = "story"

    def to_menu(self):
        with self._lock:
            self.saved = self._load()
            self._fresh_state()
            self._reset()
            self.stage = "title"

    def buy(self, uid):
        with self._lock:
            sim = self.session.sim
            if self.stage != "shop" or sim.phase != "shop":
                return False
            if uid in CORE_NAMES:
                self.inputs.buy(uid)  # luật Shop của sim xử lý ở tick kế (bought / buy_failed)
                return True
            if uid not in GEAR:
                return False
            lv = self.gear[uid]
            costs = GEAR[uid][2]
            if lv >= len(costs) or sim.money < costs[lv]:
                return False
            sim.money -= costs[lv]  # đồ nghề sáng tạo: trừ ví, có hiệu lực từ Ngày kế
            self.gear[uid] = lv + 1
            return True

    def restart(self):
        """R: chơi lại Ngày hiện tại từ đầu (trạng thái đầu Ngày)."""
        with self._lock:
            if self.stage in ("gather", "quan", "eveningintro", "dayintro"):
                self.history = self.history[: self.start_day - 1]
                self._reset()
                self.stage = "dayintro"

    # --- trạng thái cho client -------------------------------------------------------------------
    def _shop(self):
        sim = self.session.sim
        out = []
        for uid, (name, desc) in CORE_NAMES.items():
            levels = self.base_tuning["shop"]["upgrades"][uid]
            lv = sim.upgrades.get(uid, 0)
            field = "oxygen_max_s" if uid == "oxygen" else "hp_max"
            nxt = levels[lv] if lv < len(levels) else None
            d = desc + (f" → {nxt[field]}{' giây' if uid == 'oxygen' else ' Máu'}" if nxt else "")
            out.append({"id": uid, "name": name, "desc": d, "level": lv, "max": len(levels),
                        "cost": nxt["price"] if nxt else None, "core": True})
        for uid, (name, desc, costs) in GEAR.items():
            lv = self.gear[uid]
            out.append({"id": uid, "name": name, "desc": desc, "level": lv, "max": len(costs),
                        "cost": costs[lv] if lv < len(costs) else None, "core": False})
        return out

    def state_json(self) -> bytes:
        with self._lock:
            sess = self.session
            sim = sess.sim
            snap = sess.snapshot()
            t = sim.tuning
            snap["meta"] = dict(t.get(sim.phase, {}))
            snap["menu"] = t["menu"]
            snap["freshness"] = t["freshness"]
            snap["events"] = list(self.events)
            snap["finished"] = sess.done
            snap["paused"] = sess.paused
            snap["error"] = self.error
            snap["campaign"] = {
                "stage": self.stage, "day": sim.day, "max_days": MAX_DAYS, "goal": GOAL,
                "intro_left": max(0, INTRO_TICKS - self.intro_ticks), "shop": self._shop(), "gear": self.gear,
                "today": self.today, "history": self.history, "can_continue": bool(self.saved),
                "saved_day": self.saved["day"] if self.saved else None,
            }
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class _QuietServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if not isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            super().handle_error(request, client_address)


class _CampaignHandler(_Handler):
    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path not in ("/next", "/new", "/buy", "/menu", "/quit"):
            super().do_POST()
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        raw = self.rfile.read(min(max(n, 0), 4096)) if n else b""
        if path == "/next":
            self.game.next_stage()
        elif path == "/new":
            self.game.new_game()
        elif path == "/menu":
            self.game.to_menu()
        elif path == "/quit":
            self._send(200, b'{"ok":true}')
            self.game.quit_requested.set()
            return
        else:
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
                uid = body.get("id") if isinstance(body, dict) else None
            except (ValueError, UnicodeDecodeError):
                uid = None
            ok = self.game.buy(uid)
            self._send(200 if ok else 400, b'{"ok":true}' if ok else b'{"ok":false}')
            return
        self._send(200, b'{"ok":true}')


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.play", description="Quán Ăn Chợ Nổi — mùa nước nổi 5 Ngày trên trình duyệt.")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--save-dir", dest="save_dir", default="saves")
    p.add_argument("--export-leaderboard", dest="export_leaderboard",
                   help="xuất bảng xếp hạng cục bộ đã sắp ra file JSON rồi thoát")
    p.add_argument("--leaderboard", default=None, help="file store bảng xếp hạng (mặc định leaderboard.json)")
    a = p.parse_args(argv)
    if a.export_leaderboard:
        from .leaderboard import DEFAULT_STORE, export as export_board
        try:
            export_board(a.leaderboard or DEFAULT_STORE, a.export_leaderboard)
        except BadInput as e:
            sys.stderr.write(f"đầu vào sai: {e}\n")
            return 2
        except OSError as e:
            sys.stderr.write(f"lỗi ghi: {e}\n")
            return 1
        return 0
    try:
        tuning = load_contract()["tuning"]
        game = CampaignGame(tuning, a.seed, a.save_dir)
        handler = type("Handler", (_CampaignHandler,), {"game": game})
        httpd = _QuietServer((a.host, a.port), handler)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    game.start()
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    print(f"Quán Ăn Chợ Nổi — mở trình duyệt tại http://{a.host}:{httpd.server_address[1]}/  (Ctrl+C để dừng)",
          flush=True)
    try:
        while not game.quit_requested.wait(0.5):
            pass
        print("Đã thoát game.", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()
        httpd.server_close()
        game.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
