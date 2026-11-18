

from typing import Any

from sqlalchemy.orm import Session
from app.crud import order as crud_order
from app.crud import book as crud_book
from app.models.user import User

# ==========================================
# BƯỚC 1: KHAI BÁO SCHEMA CHO LLM
# ==========================================
CHATBOT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Tra cứu trạng thái của một đơn hàng cụ thể. Chỉ dùng khi người dùng cung cấp mã đơn hàng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer", "description": "Mã số đơn hàng cần tra cứu."}
                },
                "required": ["order_id"]
            }
        }
    },
    # ... (các công cụ khác như add_to_cart)
]


# ==========================================
# BƯỚC 2: HÀM THỰC THI LOGIC KHI LLM GỌI TOOL
# ==========================================
def execute_tool(
    function_name: str,
    arguments: dict[str, Any],
    db: Session,
    current_user: User | None,
) -> dict[str, Any]:
    """Thực thi tool an toàn với context của người dùng hiện tại."""

    if function_name == "get_order_status":
        if not current_user:
            return {"error": "Vui lòng đăng nhập để tra cứu đơn hàng."}

        order_id = arguments.get("order_id")
        if not isinstance(order_id, int) or isinstance(order_id, bool) or order_id < 1:
            return {"error": "Mã đơn hàng phải là số nguyên dương."}

        order = crud_order.get_order(db, order_id=order_id)

        # BẢO MẬT: Chặn xem đơn của người khác
        if not order or order.user_id != current_user.id:
            return {"error": f"Không tìm thấy đơn hàng #{order_id} của bạn."}

        return {
            "order_id": order.id,
            "status": order.status,
            "total": float(order.total)
        }

    # ... (xử lý add_to_cart)

    return {"error": f"Tool {function_name} chưa được hỗ trợ."}