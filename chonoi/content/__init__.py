"""Gói nội dung & sáng tạo (MR-1) của Quán Ăn Chợ Nổi — lấy cảm hứng từ Dave the Diver.

Tách biệt hoàn toàn khỏi lõi mô phỏng headless (`chonoi.sim.*`):
- Không thay đổi tick, sự kiện, tiền, uy tín hay snapshot của Test Contract v1.0.
- Chỉ dùng ở tầng client/UI, sổ tay lore và đánh giá sau ca (tắt mặc định ở headless).
"""

from .dave_theme import (
    CHONOISTA_TIERS,
    DISH_LORE,
    EVENT_DIALOGUES,
    INGREDIENT_GUIDE,
    ServiceReviewTracker,
    dialogue_for_event,
    summarize_shift_review,
)

__all__ = [
    "CHONOISTA_TIERS",
    "DISH_LORE",
    "EVENT_DIALOGUES",
    "INGREDIENT_GUIDE",
    "ServiceReviewTracker",
    "dialogue_for_event",
    "summarize_shift_review",
]
