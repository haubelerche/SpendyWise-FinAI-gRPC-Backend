import uuid
from typing import Optional, Any

from app.schemas.achievement import Achievement, AchievementCreate, AchievementUpdate, AchievementResponse
from app.db.supabase_client import get_supabase_client
from supabase import Client

# Khởi tạo client Supabase (cấu hình trong file config hoặc môi trường)
supabase: Client = get_supabase_client()

class AchievementModel:
    @staticmethod
    def create_achievement(data: AchievementCreate) -> Achievement:
        # Chuyển đổi data thành dict để phù hợp với Supabase
        achievement_data = data.model_dump(exclude_unset=True)
        # Thêm achievement_id nếu chưa có (Supabase sẽ tự sinh nếu để null)
        if "achievement_id" not in achievement_data or achievement_data["achievement_id"] is None:
            achievement_data["achievement_id"] = str(uuid.uuid4())

        # Lưu vào Supabase
        response: Any = supabase.table("achievement").insert(achievement_data).execute()
        if response.data:
            return Achievement(**response.data[0])
        raise ValueError("Failed to create achievement")

    @staticmethod
    def update_achievement(achievement_id: uuid.UUID, data: AchievementUpdate) -> Achievement:
        # Chuyển đổi data thành dict, loại bỏ các trường không được cập nhật
        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            raise ValueError("No updates provided")

        # Cập nhật trong Supabase
        response: Any = supabase.table("achievement").update(update_data).eq("achievement_id", str(achievement_id)).execute()
        if response.data:
            return Achievement(**response.data[0])
        raise ValueError(f"Achievement with ID {achievement_id} not found")

    @staticmethod
    def get_achievement(achievement_id: uuid.UUID) -> Optional[AchievementResponse]:
        # Lấy dữ liệu từ Supabase
        response: Any = supabase.table("achievement").select("*").eq("achievement_id", str(achievement_id)).execute()
        if response.data and len(response.data) > 0:
            achievement_data = response.data[0]
            return AchievementResponse(**achievement_data)
        return None  # Trả về None nếu không tìm thấy