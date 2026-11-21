"""Nội dung sáng tạo MR-1 lấy cảm hứng từ *Dave the Diver* cho Quán Ăn Chợ Nổi.

Tinh thần *Dave the Diver* phiên bản miền Tây Nam Bộ:
- **Sáng lặn sông Chín Khúc (Blue Hole -> Sông Chín Khúc)**: Sổ tay phân tầng độ sâu
  (`INGREDIENT_GUIDE`) cho 4 nguyên liệu cốt lõi.
- **Tối mở nhà bè Má Tư (Bancho Sushi -> Quán Út Sen)**: Sổ tay thực đơn (`DISH_LORE`),
  câu thoại giọng Nam Bộ phản ứng theo từng sự kiện bếp/bàn (`EVENT_DIALOGUES`).
- **Chợ Nổi Review (lấy cảm hứng từ app Cooksta)**: `ServiceReviewTracker` theo dõi chuỗi
  phục vụ được boa (Bancho Streak) và xếp hạng sao cho quán chỉ bằng cách ĐỌC event stream,
  tắt hoàn toàn ở chế độ headless nên không làm lệch Test Contract v1.0.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


INGREDIENT_GUIDE: Dict[str, Dict[str, object]] = {
    "bong_dien_dien": {
        "name": "Bông điên điển",
        "depth_zone": "Tầng mặt (0 m)",
        "rarity": "Mùa nước nổi",
        "description": "Vàng rực ven bờ dừa nước, giòn ngọt, linh hồn của nồi lẩu cá linh.",
        "tip": "Hái nhanh trên mặt nước bằng phím E, nhớ canh nhịp mọc lại 20 giây.",
    },
    "bong_sung": {
        "name": "Bông súng",
        "depth_zone": "Tầng mặt (0 m)",
        "rarity": "Phổ biến",
        "description": "Cọng giòn mát mọc dọc rạch Sen, bóp gỏi chua ngọt khách rất mê.",
        "tip": "Cần 2 bông cho một đĩa gỏi bông súng — hái cặp rất lợi ô giỏ.",
    },
    "ca_linh": {
        "name": "Cá linh non",
        "depth_zone": "Tầng nông & trung (5–10 m)",
        "rarity": "Theo đàn",
        "description": "Bơi thành đàn óng ánh mùa nước nổi, béo mềm không cần đánh vảy.",
        "tip": "Một cú bắt (Space) thu trọn 3 con — vừa khít công thức nồi lẩu!",
    },
    "ca_loc": {
        "name": "Cá lóc đồng",
        "depth_zone": "Tầng trung & sâu (10–16 m)",
        "rarity": "Đặc sản tầng sâu",
        "description": "Chắc thịt, ẩn sâu dưới đáy phù sa; nướng trui rơm thơm nức nhà bè.",
        "tip": "Chú ý thanh oxy khi lặn xuống 16 m, đừng tham mà ngất mất sạch giỏ!",
    },
}


DISH_LORE: Dict[str, Dict[str, object]] = {
    "ca_loc_nuong_trui": {
        "name": "Cá lóc nướng trui",
        "tagline": "Thơm mùi rơm mới, chấm mắm me hết sẩy!",
        "chef_note": "Má Tư dặn trở đều tay đúng 6 giây cho da cháy xém mà thịt còn mọng.",
        "bancho_rank": "Món tủ nhà bè",
    },
    "goi_bong_sung": {
        "name": "Gỏi bông súng",
        "tagline": "Giòn rụm mát ruột, lên món nhanh nhất quán!",
        "chef_note": "Chỉ mất 4 giây trộn — cứu nguy cực tốt khi khách sắp cạn kiên nhẫn.",
        "bancho_rank": "Khai vị tốc độ",
    },
    "lau_ca_linh_dien_dien": {
        "name": "Lẩu cá linh bông điên điển",
        "tagline": "Đệ nhất đặc sản mùa nước nổi Chợ Nổi Rạch Sen!",
        "chef_note": "Nấu 10 giây nhưng giá cao nhất (120k) — giữ khách vui để ăn trọn tiền boa!",
        "bancho_rank": "Đặc sản 5 sao",
    },
}


EVENT_DIALOGUES: Dict[str, List[str]] = {
    "cook_started": [
        "Út Sen: Dạ có liền nha cô chú, lửa bếp B1 cháy rực rồi!",
        "Má Tư: Bỏ đúng nguyên liệu tươi mới bắt hồi sáng, thơm phức luôn con!",
    ],
    "dish_ready": [
        "Bếp B1: Ting! Món chín nóng hổi rồi, bưng ra liền Út ơi!",
        "Má Tư: Món lên mâm đẹp quá trời, bưng lẹ kẻo khách đợi!",
    ],
    "dish_picked": [
        "Út Sen: Hây da, bưng chắc tay chạy ra bàn T1 nào!",
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
