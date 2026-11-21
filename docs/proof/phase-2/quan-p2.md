# Bằng chứng kiểm chứng Phase 2 — `quan` & MR-1 (Nguyễn Thanh Tùng)

## Lệnh chạy kiểm chứng
```powershell
$env:PYTHONPATH="tests;."; python -m unittest tests.test_quan_lat4 tests.test_quan_p2 tests.test_python_starter_units tests.test_team_check -v
```

## Kết quả chạy thật
```text
test_guides_cover_all_core_ingredients_and_dishes (tests.test_quan_lat4.TestMR1DaveTheDiverContent) ... ok
test_review_tracker_disabled_by_default_for_headless (tests.test_quan_lat4.TestMR1DaveTheDiverContent) ... ok
test_review_tracker_summarizes_events_when_enabled (tests.test_quan_lat4.TestMR1DaveTheDiverContent) ... ok
test_ac_p1_12_cook_oldest_reserved_and_ready_ticks (tests.test_quan_lat4.TestQuanLat4Cooking) ... ok
test_ac_p1_12_interact_priority_stove_before_table_and_no_fallthrough (tests.test_quan_lat4.TestQuanLat4Cooking) ... ok
test_ac_p1_14_finish_eating_pays_and_clamps_reputation (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_ac_p1_14_serve_on_last_tick_pays_closing_and_emits_quan_end (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_ac_p1_14_waiting_customer_at_closing_no_rep_penalty_and_cleans_stove (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_headless_cli_full_lat4_loop_deterministic (tests.test_quan_lat4.TestQuanLat4PaymentAndClosing) ... ok
test_ac_p1_13_pick_and_serve_with_tip (tests.test_quan_lat4.TestQuanLat4PickServeTip) ... ok
test_ac_p1_13_serve_on_exact_zero_patience_tick_still_valid_with_zero_tip (tests.test_quan_lat4.TestQuanLat4PickServeTip) ... ok
test_phase2_guides_and_review_tracker (tests.test_quan_p2.TestMR1Phase2DaveContent) ... ok
test_burn_at_1201_re_reserves_or_marks_unfulfillable (tests.test_quan_p2.TestQuanPhase2BurnExtension) ... ok
test_exact_1200_ticks_still_pickable (tests.test_quan_p2.TestQuanPhase2BurnExtension) ... ok
test_two_stoves_cook_in_order_and_lau_mam_price_tip (tests.test_quan_p2.TestQuanPhase2MultiStoveMenu) ... ok
test_customer_schedule_smallest_table_and_day_plan_filter (tests.test_quan_p2.TestQuanPhase2ScheduleAndDayPlan) ... ok
test_no_dish_when_plan_dishes_lack_stock_even_if_other_dish_has_stock (tests.test_quan_p2.TestQuanPhase2ScheduleAndDayPlan) ... ok
test_bad_frames_raise (tests.test_python_starter_units.Units) ... ok
test_catch_is_a_v10_button_and_attack_is_not (tests.test_python_starter_units.Units) ... ok
test_id_allocator_continues_after_max (tests.test_python_starter_units.Units) ... ok
test_id_sorting (tests.test_python_starter_units.Units) ... ok
test_input_edges_and_inherit (tests.test_python_starter_units.Units) ... ok
test_live_inputs_keep_fast_tap_edge (tests.test_python_starter_units.Units) ... ok
test_session_steps_gather_and_dock (tests.test_python_starter_units.Units) ... ok
test_good (tests.test_team_check.TeamCheck) ... ok
test_template_is_rejected (tests.test_team_check.TeamCheck) ... ok
test_too_few_members (tests.test_team_check.TeamCheck) ... ok
test_wrong_size_duplicate_and_outsider (tests.test_team_check.TeamCheck) ... ok

----------------------------------------------------------------------
Ran 28 tests in 0.486s

OK
```
