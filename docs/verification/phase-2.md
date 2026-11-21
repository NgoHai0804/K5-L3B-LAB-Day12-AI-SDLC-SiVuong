# Ma trận truy vết Phase 2 (TICKET-02 · Contract v1.1 → nay v1.3)

> Trạng thái cuối: Phase 2 đã được **nâng lên Contract v1.3** (v1.3 = v1.2 gameplay/tuning/kho/JSONL + `bench_cmd`/`soak_cmd`).
> Bằng chứng JSONL trong `docs/proof/phase-2/` là bản chạy **đúng contract v1.1** lúc gắn tag. Test hiện hành đã gộp vào
> `tests/test_rules_p2p3.py` (luật) và `tests/test_phase2_son.py` (manifest/pause/CLI `day`).

| AC | Nội dung (TICKET-02 / Contract v1.1) | Cách kiểm chứng (test hiện hành) | Bằng chứng | Kết quả |
|---|---|---|---|---|
| AC-P2-01 | Tuning v1.1: `contract_version`, `fish_yield` 3 loài, N5/N6 `keo_neo`, `fish_initial` ≥ 8 | `tests/test_phase4.py::ContractV13::test_version_extensions_and_commands`, `::test_v12_gameplay_kept`; `chonoi/contract.py::SUPPORTED_VERSIONS` | `game.contract.json` · [`out-gather-p2.jsonl`](../proof/phase-2/out-gather-p2.jsonl) (6 nút N1–N6, 8 đàn F1–F8) | Đạt (đã tiến lên v1.3, tương thích ngược v1.1) |
| AC-P2-02 | Cá bơi 1.5 m/s, đổi hướng bước 120, phản xạ mép/dải loài; sinh đầu ca 8 → trần 12, mỗi 360 tick ≤ 1, khoảng cách > 1 m, trọng số 40/30/30 | `tests/test_rules_p2p3.py::FishAndMonsters` (`test_initial_fish_and_spawn_schedule`, `test_fish_stays_in_species_band`, `test_m2_from_day_3_only_in_layout`) | [`out-gather-p2.jsonl`](../proof/phase-2/out-gather-p2.jsonl) | Đạt |
| AC-P2-03 | Cá Sấu Năm Chèo: `patrol/chase`, chặn biên/dải, hit −1 HP + mất `floor(hold/2)` LIFO + bất tử `invuln_ticks`, recoil `recoil_ticks` | `tests/test_rules_p2p3.py::FishAndMonsters` (`test_monster_hit_loses_half_lifo_invuln_recoil`, `test_no_hit_in_shallow_water`, `test_patrol_and_chase`) | [`out-gather-p2.jsonl`](../proof/phase-2/out-gather-p2.jsonl) | Đạt |
| AC-P2-04 | Máu/ngất do quái: HP 0 ⇒ `faint {cause:"monster"}` bỏ toàn bộ giỏ, mở quán với kho rỗng | `tests/test_rules_p2p3.py::FishAndMonsters::test_monster_faint_drops_all` | [`out-gather-p2.jsonl`](../proof/phase-2/out-gather-p2.jsonl) | Đạt |
| AC-P2-05..07 | 2 bếp (`B1,B2`), 4 bàn (`T1–T4`); 6 món + `ca_keo`/`keo_neo` dữ liệu; `day_plan` D1–D5, lọc menu theo kế hoạch trước kho; `no_dish` khi thiếu món | `tests/test_rules_p2p3.py::DayLoop` (`test_day_plan_menu_filter`, `test_day_start_events_and_plan`) | `game.contract.json` (`quan.stoves/tables/menu/day_plan`) | Đạt |
| AC-P2-08 | Vòng `day`: `gather → quan → shop`, bàn giao kho cùng tick chuyển pha, `days_completed`/`reason:"days_complete"` | `tests/test_rules_p2p3.py::DayLoop` (`test_handover_shop_buy_and_next_day_upgrade`, `test_shop_auto_close_and_days_complete`) | `tests/test_rules_p2p3.py` | Đạt |
| AC-P2-09 | Shop: mua `oxygen`/`hp` theo cấp, hiệu lực Ngày kế; `buy_failed` khi thiếu tiền/tối đa; tự đóng sau `max_ticks` | `tests/test_rules_p2p3.py::DayLoop::test_handover_shop_buy_and_next_day_upgrade`; `tests/test_play.py::CampaignTest::test_core_buy_goes_through_sim_and_gear_changes_next_day` | `tests/test_play.py` | Đạt |
| AC-P2-10..12 | Manifest v1.1 (nút/pause/`buy`/`day --days`), pause đóng băng timer, HUD quán | `tests/test_phase2_son.py::Manifest`, `::DayCli`, `::Pause` | [`son-contract-pause.md`](../proof/phase-2/son-contract-pause.md) | Đạt |
| AC-P2-11,13 | HUD sáng + smoke tích hợp `gather → kho → quan` + regression P1 | `tests/test_smoke_p1.py::Integration` | [`quan-p2.jsonl`](../proof/phase-2/quan-p2.jsonl) (`stock {"bong_sung":2,"ca_loc":1}` tick 0), [`gather-p2.jsonl`](../proof/phase-2/gather-p2.jsonl) | Đạt |
| AC-P2-EX-04 | Cháy món (`burn_s` hữu hạn, `ready_ticks > 1200` ⇒ `dish_burnt`, re-reserve) | Lõi để `burn_s: null` — **không bật tính năng cháy** | `game.contract.json` (`quan.burn_s: null`) | Không bật ở lõi (đúng DoD) |
| AC-P2-MR1 | Nội dung sáng tạo cảm hứng *Dave the Diver* | Bản main cuối **gỡ module nội dung MR-1**; phần sáng tạo thay bằng "Mùa nước nổi"/Sprint/đồ nghề ở Phase 4 | `README.md` mục "Sáng tạo của nhóm" | Đã thay bằng mở rộng Phase 4 |

## Thay đổi test P1 (có lý do)
- `tests/test_smoke_p1.py`: `len(fish)` **6 → 8** — chuẩn v1.1 (TICKET-02 §1.2). Không phải nới test cho xanh.
- `tests/test_rules_p1.py`: fixture cập nhật theo schema kho/giá về sau (v1.2–v1.3); đầu file có ghi lý do.
- `game.contract.json` `contract_version`: `"1.1"` → (Phase 3) `"1.2"` → (Phase 4) `"1.3"`, tương thích ngược.

## Đánh giá ngắn
- Đạt: Lát 1 (AC-P2-01..02, Hải), Cá Sấu/Máu (AC-P2-03..04), lõi `quan` v1.1 + `day_plan` (AC-P2-05..07), vòng `day` + Shop (AC-P2-08..09), manifest/pause/HUD (AC-P2-10..12), smoke + regression (AC-P2-11,13). Toàn bộ suite hiện hành **116/116 xanh**.
- Chưa bật ở lõi: Cháy món (AC-P2-EX-04, `burn_s: null`). MR-1 (Dave content) đã gỡ ở bản cuối.
- Cần chỉnh: giữ `docs/contracts/` đồng bộ với schema cá thể (đã cập nhật ở Phase 3).
