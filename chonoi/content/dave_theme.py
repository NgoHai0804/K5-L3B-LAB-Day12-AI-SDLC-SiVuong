"""Nội dung sáng tạo MR-1 (Phase 1 & Phase 2) lấy cảm hứng từ *Dave the Diver* cho Quán Ăn Chợ Nổi.

Tinh thần *Dave the Diver* phiên bản miền Tây Nam Bộ:
- **Sáng lặn sông Chín Khúc (Blue Hole -> Sông Chín Khúc)**: Sổ tay phân tầng độ sâu
  (`INGREDIENT_GUIDE`) cho đủ 6 nguyên liệu Phase 2 và sổ tay thủy quái / cá hiếm (`CREATURE_GUIDE`:
  Cá Sấu Năm Chèo, Rắn Hổ Mây, Cá Hô Khổng Lồ).
- **Tối mở nhà bè Má Tư (Bancho Sushi -> Quán Út Sen)**: Sổ tay thực đơn 6 món (`DISH_LORE`),
  lời dặn đầu 5 Ngày của Má Tư (`DAY_STORY_BRIEFS`), mô tả Shop & Chợ Chú Sáu (`SHOP_LORE`)
  và câu thoại giọng Nam Bộ phản ứng theo từng sự kiện (`EVENT_DIALOGUES`).
- **Chợ Nổi Review (lấy cảm hứng từ app Cooksta)**: `ServiceReviewTracker` theo dõi chuỗi
  phục vụ được boa (Bancho Streak), ảnh Cá Hô và xếp hạng sao cho quán chỉ bằng cách ĐỌC event stream,
  tắt hoàn toàn ở chế độ headless nên không làm lệch Test Contract v1.0 / v1.1.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


INGREDIENT_GUIDE: Dict[str, Dict[str, object]] = {
    "bong_dien_dien": {
        "name": "Bông điên điển",
        "depth_zone": "Tầng mặt (0 m)",
        "rarity": "Mùa nước nổi",
        "description": "Vàng rực ven bờ dừa nước, giòn ngọt, linh hồn của nồi lẩu cá linh và canh chua.",
        "tip": "Hái nhanh trên mặt nước ở N1/N2 bằng phím E, mọc lại sau 20 giây.",
    },
    "bong_sung": {
        "name": "Bông súng",
        "depth_zone": "Tầng mặt (0 m)",
        "rarity": "Phổ biến",
        "description": "Cọng giòn mát mọc dọc rạch Sen, bóp gỏi chua ngọt khách rất mê.",
        "tip": "Hái ở N3/N4; cần 2 bông cho một đĩa gỏi bông súng.",
    },
    "keo_neo": {
        "name": "Kèo nèo",
        "depth_zone": "Tầng mặt (0 m)",
        "rarity": "Rau đồng sâu bờ",
        "description": "Rau cọng giòn đặc sản miền Tây, ăn kèm lẩu mắm là hết bài.",
        "tip": "Mọc ở đoạn sông xa (N5 [76,0], N6 [90,0]) — tiện ghé hái khi đi săn cá kèo.",
    },
    "ca_linh": {
        "name": "Cá linh non",
        "depth_zone": "Tầng nông & trung (3–12 m)",
        "rarity": "Theo đàn (yield 3)",
        "description": "Bơi thành đàn óng ánh mùa nước nổi, béo mềm không cần đánh vảy.",
        "tip": "Một cú bắt (Space) thu trọn 3 con — vừa khít nồi lẩu cá linh hoặc dư cho lẩu mắm!",
    },
    "ca_loc": {
        "name": "Cá lóc đồng",
        "depth_zone": "Tầng trung (8–20 m)",
        "rarity": "Đặc sản tầng trung (yield 1)",
        "description": "Chắc thịt, lẩn ở tầng trung; nướng trui rơm hay nấu canh chua đều thơm nức nhà bè.",
        "tip": "Chú ý Cá Sấu Năm Chèo bắt đầu tuần tra từ độ sâu 10 m trở xuống.",
    },
    "ca_keo": {
        "name": "Cá kèo",
        "depth_zone": "Tầng sâu (22–28 m)",
        "rarity": "Đặc sản tầng sâu (yield 2)",
        "description": "Loài cá nhỏ béo bùi dưới tầng sâu phù sa, nướng muối ớt hay thả lẩu mắm đều tuyệt hảo.",
        "tip": "Sống sâu 22–28 m cùng lãnh địa Cá Sấu — nên nâng cấp Bình oxy và Áo phao trước Ngày 3!",
    },
}


DISH_LORE: Dict[str, Dict[str, object]] = {
    "ca_loc_nuong_trui": {
        "name": "Cá lóc nướng trui",
        "tagline": "Thơm mùi rơm mới, chấm mắm me hết sẩy!",
        "chef_note": "Má Tư dặn trở đều tay đúng 6 giây (60k) cho da cháy xém mà thịt còn mọng.",
        "bancho_rank": "Món tủ nhà bè",
    },
    "goi_bong_sung": {
        "name": "Gỏi bông súng",
        "tagline": "Giòn rụm mát ruột, lên món nhanh nhất quán!",
        "chef_note": "Chỉ mất 4 giây trộn (40k) — cứu nguy cực tốt khi 4 bàn cùng gọi món.",
        "bancho_rank": "Khai vị tốc độ",
    },
    "lau_ca_linh_dien_dien": {
        "name": "Lẩu cá linh bông điên điển",
        "tagline": "Đệ nhất đặc sản mùa nước nổi Chợ Nổi Rạch Sen!",
        "chef_note": "Nấu 10 giây (120k) — chia 2 bếp B1/B2 để vừa nấu lẩu vừa kịp ra món nhanh.",
        "bancho_rank": "Đặc sản 4 sao",
    },
    "canh_chua_ca_loc": {
        "name": "Canh chua cá lóc bông điên điển",
        "tagline": "Chua thanh vị me, ngọt thịt cá đồng, thơm nức rau ôm!",
        "chef_note": "Nấu 8 giây (90k) với 1 cá lóc + 1 điên điển — tỷ lệ lời/ô giỏ cực đẹp ở Ngày 3.",
        "bancho_rank": "Món quê đắt khách",
    },
    "ca_keo_nuong": {
        "name": "Cá kèo nướng muối ớt",
        "tagline": "Nướng than hồng xèo xèo, mặn mà cay nồng!",
        "chef_note": "Một đàn cá kèo (2 con) nấu vừa đúng 1 đĩa trong 6 giây (70k).",
        "bancho_rank": "Mồi bén tầng sâu",
    },
    "lau_mam": {
        "name": "Lẩu mắm miền Tây",
        "tagline": "Tuyệt phẩm hội tụ cả sông Chín Khúc trong một nồi lẩu!",
        "chef_note": "Nấu 12 giây, giá kỷ lục 200k (boa tới 40k!) — đừng để cháy trên bếp nếu bật chế độ khó!",
        "bancho_rank": "Tuyệt phẩm 5 sao",
    },
}


CREATURE_GUIDE: Dict[str, Dict[str, object]] = {
    "ca_sau": {
        "name": "Cá Sấu Năm Chèo",
        "depth_zone": "Tầng trung & sâu (10–30 m)",
        "danger": "Cao (truy đuổi 3.0 m/s, chạm mất 1 Máu & rơi nửa giỏ)",
        "description": "Thủy quái huyền thoại sông Chín Khúc. M1 giữ vùng sâu [60,24], từ Ngày 3 có thêm M2 [85,18].",
        "tip": "Nổi lên trên d < 10 m hoặc giữ khoảng cách > 16 m để cắt đuôi; dùng Lao xua (Q) khi đã nâng cấp.",
    },
    "ran": {
        "name": "Rắn Hổ Mây",
        "depth_zone": "Tầng trung (8–20 m)",
        "danger": "Nhanh (truy đuổi 3.5 m/s, phát hiện ≤ 8 m)",
        "description": "Loài rắn nước thoăn thoắt ẩn nấp đoạn sông [72,14]–[76,14].",
        "tip": "Cẩn thận khi săn cá lóc ở tầng trung; lên trên d < 8 m là an toàn.",
    },
    "ca_ho": {
        "name": "Cá Hô Khổng Lồ",
        "depth_zone": "Tầng trung & sâu (10–30 m)",
        "danger": "Hiền lành — loài quý cần bảo tồn",
        "description": "Vua cá sông Mekong bơi khoan thai 1.0 m/s. Lỡ bắt trúng Út Sen sẽ thả ngay về sông.",
        "tip": "Nhấn F để chụp ảnh trong ≤ 6 m — nhận ngay +0.5 uy tín (mỗi ngày 1 lần) kiểu nhiệm vụ ảnh Dave the Diver!",
    },
}


DAY_STORY_BRIEFS: Dict[int, Dict[str, str]] = {
    1: {
        "title": "Ngày 1 — Khai trương nhà bè",
        "quote": "Má Tư: Bữa đầu bán nhẹ nhàng cá lóc nướng trui với gỏi bông súng thôi nghen Út!",
    },
    2: {
        "title": "Ngày 2 — Mùa cá linh về",
        "quote": "Má Tư: Nước nổi lên rồi, cá linh nhiều lắm! Bữa nay nấu lẩu cá linh bông điên điển đãi khách!",
    },
    3: {
        "title": "Ngày 3 — Chạm đáy tìm cá kèo",
        "quote": "Má Tư: Nghe nói dưới sâu có tới hai con Cá Sấu lận đó, con nhớ sắm bình oxy với áo phao nha!",
    },
    4: {
        "title": "Ngày 4 — Nồi lẩu mắm trứ danh",
        "quote": "Má Tư: Hôm nay nhà bè mở bán Lẩu Mắm Miền Tây — nhớ hái kèo nèo tận cuối rạch về mới đúng vị!",
    },
    5: {
        "title": "Ngày 5 — Đêm hội Chợ Nổi Rạch Sen",
        "quote": "Má Tư: Đêm cuối cùng rồi con ơi, bật cả hai bếp B1–B2 lên cho rực rỡ chợ nổi nào!",
    },
}


SHOP_LORE: Dict[str, Dict[str, str]] = {
    "oxygen": {
        "name": "Bình oxy",
        "description": "Bình hơi tự chế của chú Sáu giúp Út Sen lặn sâu 45 s (Cấp 1) tới 60 s (Cấp 2).",
    },
    "hp": {
        "name": "Áo phao",
        "description": "Áo phao bông gòn dày dặn, nâng Máu tối đa lên 4 (Cấp 1) và 5 (Cấp 2) chống Cá Sấu.",
    },
    "weapon": {
        "name": "Lao xua (Q)",
        "description": "Đẩy lùi và làm choáng thủy quái — cảm hứng trực tiếp từ cây lao huyền thoại của Dave!",
    },
    "net": {
        "name": "Vợt hút cá",
        "description": "Tăng tầm bắt và gom 2–3 đàn cá trong một cú Space.",
    },
    "vendor": {
        "name": "Chợ Chú Sáu",
        "description": "Mua bán nguyên liệu dư ngay tại Shop; hàng mua được giao thẳng vào bếp tối hôm sau.",
    },
}


EVENT_DIALOGUES: Dict[str, List[str]] = {
    "cook_started": [
        "Út Sen: Dạ có liền nha cô chú, nổi lửa bếp nhà bè rồi!",
        "Má Tư: Bỏ đúng nguyên liệu tươi mới bắt hồi sáng, thơm phức luôn con!",
    ],
    "dish_ready": [
        "Bếp: Ting! Món chín nóng hổi rồi, bưng ra liền Út ơi!",
        "Má Tư: Món lên mâm đẹp quá trời, bưng lẹ kẻo khách đợi!",
    ],
    "dish_burnt": [
        "Má Tư: Úi trời ơi khét lẹt rồi Út ơi! Mau dọn chảo nấu lại phần mới liền!",
    ],
    "dish_picked": [
        "Út Sen: Hây da, bưng chắc tay chạy ra bàn nào!",
    ],
    "served": [
        "Khách: Chà, thơm nức mũi luôn! Cảm ơn Út Sen nghen!",
    ],
    "paid_tip": [
        "Khách: Ngon bá cháy! Gửi Út thêm chút tiền boa uống nước mía nè!",
        "Má Tư: Giỏi lắm con gái, khách khen tấm tắc cho boa luôn kìa!",
    ],
    "paid_normal": [
        "Khách: No căng bụng rồi, hẹn tối mai ghé nhà bè nữa nha!",
    ],
    "customer_left_patience": [
        "Khách: Đợi lâu quá trời, thôi tui chèo ghe sang quán khác vậy...",
    ],
    "monster_hit": [
        "Út Sen: Á! Cá Sấu Năm Chèo! Rơi mất mớ cá rồi, ngoi lên thôi!",
    ],
    "photo": [
        "Út Sen: Tách! Chụp được Cá Hô khổng lồ rồi, đăng Chợ Nổi Review là nổi rần rần!",
    ],
    "released": [
        "Út Sen: Ủa Cá Hô quý hiếm nè, thả em về sông Chín Khúc nha!",
    ],
    "bought": [
        "Chú Sáu: Chốt đơn! Mai sáng đồ nghề mới phát huy công lực liền nghen Út!",
    ],
    "quan_end": [
        "Má Tư: Tắt đèn dây nghỉ tay thôi Út ơi, mai sáng lại ra sông sớm!",
    ],
}


CHONOISTA_TIERS = (
    (0, "Quán Mới Mở Bến", "★☆☆☆☆"),
    (1, "Quán Quen Rạch Sen", "★★☆☆☆"),
    (3, "Đặc Sản Chợ Nổi", "★★★☆☆"),
    (5, "Bếp Vàng Miền Tây", "★★★★☆"),
    (8, "Huyền Thoại Sông Chín Khúc", "★★★★★"),
)


def dialogue_for_event(event_name: str, data: Optional[dict] = None, index: int = 0) -> Optional[str]:
    """Trả câu thoại giọng Nam Bộ tương ứng với một sự kiện của sim (chỉ dùng cho UI)."""
    data = data or {}
    key = event_name
    if event_name == "paid":
        key = "paid_tip" if (data.get("tip") or 0) > 0 else "paid_normal"
    elif event_name == "customer_left" and data.get("reason") == "patience":
        key = "customer_left_patience"
    lines = EVENT_DIALOGUES.get(key)
    if not lines:
        return None
    return lines[index % len(lines)]


@dataclass
class ServiceReviewTracker:
    """Bộ đếm Chợ Nổi Review (kiểu Cooksta trong Dave the Diver) — chỉ ĐỌC event stream.

    Hoàn toàn tách khỏi `QuanSim`: chỉ chạy khi bật ở client/preview, tắt mặc định ở headless.
    """

    enabled: bool = False
    served_count: int = 0
    tipped_count: int = 0
    left_unhappy_count: int = 0
    burnt_count: int = 0
    photos_taken: int = 0
    tip_streak: int = 0
    best_tip_streak: int = 0
    total_tips: int = 0
    review_likes: int = 0
    highlights: List[str] = field(default_factory=list)

    def observe(self, event_name: str, data: Optional[dict] = None) -> Optional[str]:
        """Quan sát một sự kiện từ sim. Khi `enabled=False` (headless), không làm gì cả."""
        if not self.enabled:
            return None
        data = data or {}
        if event_name == "served":
            self.served_count += 1
        elif event_name == "paid":
            tip = int(data.get("tip") or 0)
            if tip > 0:
                self.tipped_count += 1
                self.tip_streak += 1
                self.best_tip_streak = max(self.best_tip_streak, self.tip_streak)
                self.total_tips += tip
                self.review_likes += 2
                if self.tip_streak >= 2:
                    self.highlights.append(f"Chuỗi phục vụ có boa ×{self.tip_streak}!")
            else:
                self.tip_streak = 0
                self.review_likes += 1
        elif event_name == "customer_left" and data.get("reason") == "patience":
            self.left_unhappy_count += 1
            self.tip_streak = 0
            self.review_likes = max(0, self.review_likes - 2)
        elif event_name == "dish_burnt":
            self.burnt_count += 1
            self.tip_streak = 0
            self.review_likes = max(0, self.review_likes - 1)
        elif event_name == "photo":
            self.photos_taken += 1
            self.review_likes += 3
            self.highlights.append("Ảnh Cá Hô gây sốt trên Chợ Nổi Review!")
        return dialogue_for_event(event_name, data, index=self.served_count + self.tipped_count)

    def tier(self) -> Dict[str, str]:
        title, stars = CHONOISTA_TIERS[0][1], CHONOISTA_TIERS[0][2]
        for threshold, name, badge in CHONOISTA_TIERS:
            if self.review_likes >= threshold:
                title, stars = name, badge
        return {"title": title, "stars": stars}

    def summary(self) -> Dict[str, object]:
        t = self.tier()
        return {
            "enabled": self.enabled,
            "tier_title": t["title"],
            "tier_stars": t["stars"],
            "review_likes": self.review_likes,
            "served_count": self.served_count,
            "tipped_count": self.tipped_count,
            "left_unhappy_count": self.left_unhappy_count,
            "burnt_count": self.burnt_count,
            "photos_taken": self.photos_taken,
            "best_tip_streak": self.best_tip_streak,
            "total_tips": self.total_tips,
            "highlights": list(self.highlights),
        }


def summarize_shift_review(event_rows: Iterable[dict], enabled: bool = True) -> Dict[str, object]:
    """Tổng hợp báo cáo Chợ Nổi Review từ danh sách dòng event JSONL (không sửa dữ liệu sim)."""
    tracker = ServiceReviewTracker(enabled=enabled)
    for row in event_rows:
        if row.get("type") == "event":
            tracker.observe(row.get("name", ""), row.get("data"))
    return tracker.summary()
