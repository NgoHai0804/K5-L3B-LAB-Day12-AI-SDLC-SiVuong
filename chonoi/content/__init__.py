"""Gói nội dung & sáng tạo (MR-1) của Quán Ăn Chợ Nổi — lấy cảm hứng từ Dave the Diver.

Tách biệt hoàn toàn khỏi lõi mô phỏng headless (`chonoi.sim.*`):
- Không thay đổi tick, sự kiện, tiền, uy tín hay snapshot của Test Contract v1.0 / v1.1 / v1.2 / v1.3.
- Chỉ dùng ở tầng client/UI, sổ tay lore, nhãn độ tươi, cảnh báo tương phản cao, phụ đề SFX và đánh giá sau ca.
"""

from .dave_theme import (
    CHONOISTA_TIERS,
    CREATURE_GUIDE,
    DAY_STORY_BRIEFS,
    DISH_LORE,
    EVENT_DIALOGUES,
    FRESHNESS_TIERS,
    HIGH_CONTRAST_WARNINGS,
    INGREDIENT_GUIDE,
    SFX_SUBTITLES,
    SHOP_LORE,
    ServiceReviewTracker,
    dialogue_for_event,
    freshness_badge,
    sfx_subtitle_for_event,
    summarize_shift_review,
)

__all__ = [
    "CHONOISTA_TIERS",
    "CREATURE_GUIDE",
    "DAY_STORY_BRIEFS",
    "DISH_LORE",
    "EVENT_DIALOGUES",
    "FRESHNESS_TIERS",
    "HIGH_CONTRAST_WARNINGS",
    "INGREDIENT_GUIDE",
    "SFX_SUBTITLES",
    "SHOP_LORE",
    "ServiceReviewTracker",
    "dialogue_for_event",
    "freshness_badge",
    "sfx_subtitle_for_event",
    "summarize_shift_review",
]
