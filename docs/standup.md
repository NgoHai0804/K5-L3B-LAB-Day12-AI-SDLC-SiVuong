# Standup giữa phase (mỗi người một dòng, 2–3 phút)

| Phase | Người | Đã xong | Sắp làm | Vướng gì |
|---|---|---|---|---|
| 1 | Đức (`tmduc23`) | Lát 2: hái nút + bắt cá + hợp đồng file kho (AC-P1-05..08); 27 test `test_gather_s2.py` xanh; chốt clarify #1–#5; bằng chứng `docs/proof/phase-1/` (chạy thật bàn giao Sáng→Tối, JSONL giống từng byte) | Điền sha commit vào `docs/members/tmduc23.md`; vai PO theo dõi Phase 2 để mở ADR nếu giảng viên đổi yêu cầu Đã tự gây 1 lỗi và hoàn nguyên: mình đọc hợp đồng ở checkout cũ, tưởng §4 buộc `hold_full` có khoá `kind`, nên thêm trường thừa vào `_try_hold` và nới `assertEqual` của Hải cho khớp. Hải phát hiện "`hold_full` thừa trường `kind`" → đã bỏ `kind`, trả test của Hải về bản gốc, sửa 2 test lát 2. Chi tiết + bài học ở `docs/clarify.md` #5. |
