# Báº±ng chá»©ng LÃ¡t 3 Phase 2 â€” 2 báº¿p/4 bÃ n + 6 mÃ³n + káº¿ hoáº¡ch ngÃ y (QuÃ½ Anh)

Dá»¯ liá»‡u: `game.contract.json` (`quan.stoves`, `quan.tables`, `menu`, `day_plan`), `chonoi/inventory.py` (`KINDS`). Code: `chonoi/sim/day_plan.py`, kiá»ƒm dá»¯ liá»‡u á»Ÿ `chonoi/contract.py`. Quyáº¿t Ä‘á»‹nh: [ADR-0001](../../adr/0001-du-lieu-quan-v11.md).

```
$ PYTHONPATH=tests:. python3 -m unittest test_quan_p2_lat3 test_quan_lat3 -v
test_ac_p2_07_contract_rejects_bad_day_plan (test_quan_p2_lat3.TestP2Lat3DayPlan.test_ac_p2_07_contract_rejects_bad_day_plan) ... ok
\u0110ã \u0111\u1ee7 s\u1ed1 su\u1ea5t d\u1ef1 ki\u1ebfn v\u1eabn g\u1ecdi ti\u1ebfp món trong k\u1ebf ho\u1ea1ch n\u1ebfu còn nguyên li\u1ec7u. ... ok
Kho \u0111\u1ee7 c\u1ea3 6 món nh\u01b0ng Ngày 1 ch\u1ec9 bán cá n\u01b0\u1edbng / g\u1ecfi súng. ... ok
Ngày 3 c\u1ea7n g\u1ecfi / canh chua / cá kèo; kho ch\u1ec9 \u0111\u1ee7 l\u1ea9u cá linh (ngoài k\u1ebf ho\u1ea1ch) -> no_dish. ... ok
test_ac_p2_07_override_and_bad_ingredients (test_quan_p2_lat3.TestP2Lat3DayPlan.test_ac_p2_07_override_and_bad_ingredients) ... ok
test_ac_p2_07_plan_d1_to_d5_matches_ticket (test_quan_p2_lat3.TestP2Lat3DayPlan.test_ac_p2_07_plan_d1_to_d5_matches_ticket) ... ok
test_ac_p2_07_slots_needed (test_quan_p2_lat3.TestP2Lat3DayPlan.test_ac_p2_07_slots_needed) ... ok
test_ac_p2_06_contract_rejects_unknown_recipe_kind (test_quan_p2_lat3.TestP2Lat3Menu.test_ac_p2_06_contract_rejects_unknown_recipe_kind) ... ok
test_ac_p2_06_each_dish_cooks_with_its_time_and_price (test_quan_p2_lat3.TestP2Lat3Menu.test_ac_p2_06_each_dish_cooks_with_its_time_and_price) ... ok
test_ac_p2_06_inventory_file_accepts_new_kinds (test_quan_p2_lat3.TestP2Lat3Menu.test_ac_p2_06_inventory_file_accepts_new_kinds) ... ok
test_ac_p2_06_menu_data_matches_ticket (test_quan_p2_lat3.TestP2Lat3Menu.test_ac_p2_06_menu_data_matches_ticket) ... ok
test_ac_p2_05_customers_fill_t1_to_t4 (test_quan_p2_lat3.TestP2Lat3StovesTables.test_ac_p2_05_customers_fill_t1_to_t4) ... ok
test_ac_p2_05_layout_from_contract (test_quan_p2_lat3.TestP2Lat3StovesTables.test_ac_p2_05_layout_from_contract) ... ok
test_ac_p2_05_stove_wins_tie_with_table (test_quan_p2_lat3.TestP2Lat3StovesTables.test_ac_p2_05_stove_wins_tie_with_table) ... ok
test_ac_p2_05_two_stoves_cook_in_parallel_oldest_first (test_quan_p2_lat3.TestP2Lat3StovesTables.test_ac_p2_05_two_stoves_cook_in_parallel_oldest_first) ... ok
test_ac_p1_11_fixture_missing_reserved_gets_recipe (test_quan_lat3.TestQuanLat3Patience.test_ac_p1_11_fixture_missing_reserved_gets_recipe) ... ok
Khách b\u1ecf v\u1ec1 nh\u1ea3 ph\u1ea7n gi\u1eef: l\u01b0\u1ee3t k\u1ebf ti\u1ebfp g\u1ecdi \u0111\u01b0\u1ee3c \u0111úng món \u0111ó. ... ok
test_ac_p1_11_patience_runs_out (test_quan_lat3.TestQuanLat3Patience.test_ac_p1_11_patience_runs_out) ... ok
test_ac_p1_11_reputation_clamped_at_min (test_quan_lat3.TestQuanLat3Patience.test_ac_p1_11_reputation_clamped_at_min) ... ok
test_ac_p1_10_dish_choice_deterministic_and_covers_menu (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_dish_choice_deterministic_and_covers_menu) ... ok
test_ac_p1_10_first_customer_reserves_recipe (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_first_customer_reserves_recipe) ... ok
L\u01b0\u1ee3t k \u1edf FIRST + k·INTERVAL l\u1ea5y bàn tr\u1ed1ng id nh\u1ecf nh\u1ea5t (T1 -> T2 -> ...), id khách n\u1ed1i ti\u1ebfp C1, C2, ... ... ok
test_ac_p1_10_no_dish_when_stock_empty (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_no_dish_when_stock_empty) ... ok
test_ac_p1_10_no_spawn_on_closing_tick (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_no_spawn_on_closing_tick) ... ok
G\u1ecfi c\u1ea7n 2 bông súng, l\u1ea9u c\u1ea7n 3 cá linh + 1 bông \u0111iên \u0111i\u1ec3n: ch\u1ec9 cá n\u01b0\u1edbng \u0111\u1ee7 kho. ... ok
test_ac_p1_10_patience_starts_next_step (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_patience_starts_next_step) ... ok
test_ac_p1_10_random_customers_false_disables_spawn (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_random_customers_false_disables_spawn) ... ok
test_ac_p1_10_schedule_uses_phase_tick_when_shift_shortened (test_quan_lat3.TestQuanLat3Schedule.test_ac_p1_10_schedule_uses_phase_tick_when_shift_shortened) ... ok
M\u1ecdi bàn \u0111\u1ec1u có khách (fixture) -> l\u01b0\u1ee3t khách b\u1ecb b\u1ecf, không phát event. ... ok
Ran 29 tests in 14.883s
OK
```

ToÃ n bá»™ bá»™ test nhÃ¡nh: `Ran 114 tests` â€” 113 Ä‘áº¡t, 1 Ä‘á» sáºµn trÃªn `main` (`test_gather_water.test_06`, Team SÃ¡ng).
