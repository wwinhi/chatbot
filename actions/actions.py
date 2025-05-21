import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

# Dữ liệu giả lập cho đơn hàng, sản phẩm và khuyến mãi
orders_status_data = {
    "1001": {"status": "Đang vận chuyển"},
    "1002": {"status": "Đã giao hàng"},
    "1003": {"status": "Hủy đơn"}
}

products_data = {
    "Samsung Galaxy S22": {"name": "Samsung Galaxy S22", "status": "Còn hàng", "warranty": {"2025-12-01": "12 tháng"}},
    "Iphone 15 Pro max": {"name": "Iphone 15 Pro max", "status": "Còn hàng", "warranty": {"2024-06-01": "12 tháng"}},
    "Xiaomi 13T": {"name": "Xiaomi 13T", "status": "Hết hàng", "warranty": {"2026-02-01": "24 tháng"}}
}

promotions = [
    {"product_category": "smartphone", "discount": "20%", "details": "Giảm giá cho tất cả điện thoại di động"},
    {"product_category": "laptop", "discount": "15%", "details": "Giảm giá cho tất cả laptop"}
]


class ActionHelloWorld(Action):
    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Chào bạn! Tôi có thể giúp gì cho bạn?")
        return []


class ActionTrackOrder(Action):
    def name(self) -> Text:
        return "action_track_order"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        order_id = next(tracker.get_latest_entity_values("order_id"), None)

        if not order_id:
            dispatcher.utter_message(text="Vui lòng cung cấp mã đơn hàng để tôi có thể kiểm tra trạng thái.")
            return [SlotSet("order_status", None)]

        # Kiểm tra trạng thái đơn hàng từ dữ liệu
        order_status = orders_status_data.get(order_id)
        if order_status:
            dispatcher.utter_message(text=f"Trạng thái đơn hàng {order_id}: {order_status['status']}")
            return [SlotSet("order_status", order_status['status'])]
        else:
            dispatcher.utter_message(
                text="Không tìm thấy thông tin về đơn hàng này. Vui lòng kiểm tra lại mã đơn hàng.")
            return []


class ActionCheckProductStatus(Action):
    def name(self) -> Text:
        return "action_check_product_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        product_name = next(tracker.get_latest_entity_values("product_name"), None)

        if not product_name:
            dispatcher.utter_message(text="Vui lòng cung cấp tên sản phẩm để tôi có thể kiểm tra trạng thái.")
            return [SlotSet("product_status", None)]

        product = products_data.get(product_name)

        if product:
            dispatcher.utter_message(text=f"Tình trạng của sản phẩm {product['name']}: {product['status']}")
            return [SlotSet("product_status", product['status'])]
        else:
            dispatcher.utter_message(
                text="Không tìm thấy thông tin về sản phẩm này. Vui lòng kiểm tra lại tên sản phẩm.")
            return []



class ActionCheckWarranty(Action):
    def name(self) -> Text:
        return "action_check_warranty"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        product_id = next(tracker.get_latest_entity_values("product_id"), None)

        if not product_id:
            dispatcher.utter_message(text="Vui lòng cung cấp mã sản phẩm để tôi có thể kiểm tra bảo hành.")
            return [SlotSet("warranty_info", None)]

        # Kiểm tra thông tin bảo hành từ dữ liệu sản phẩm
        product = products_data.get(product_id)
        if product:
            warranty_info = product['warranty']
            end_date = list(warranty_info.keys())[0]
            duration = warranty_info[end_date]
            dispatcher.utter_message(
                text=f"Sản phẩm {product['name']} có bảo hành đến {end_date}, thời gian bảo hành là {duration}.")
            return [SlotSet("warranty_info", f"Đến {end_date}, thời gian bảo hành: {duration}")]
        else:
            dispatcher.utter_message(text="Không tìm thấy thông tin bảo hành cho sản phẩm này.")
            return []



    class ActionGoToPromotionPage(Action):
        def name(self) -> Text:
            return "action_go_to_promotion_page"

        def run(self, dispatcher: CollectingDispatcher,
                tracker: Tracker,
                domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            # URL luôn luôn là trang khuyến mãi
            promotion_url = "https://ems.vlute.edu.vn/"

            # Gửi thông báo cho người dùng về trang khuyến mãi
            dispatcher.utter_message(
                text=f"Hiện tại có chương trình khuyến mãi cho các sản phẩm.\n"
                     f"Bạn có thể tham khảo thêm tại đây: {promotion_url}.")

            # Không cần SlotSet nữa vì chúng ta không lưu thông tin cụ thể của khuyến mãi
            return []

    class ActionCallOpenFaaS(Action):
        def name(self) -> str:
            return "action_call_openfaas"

        def run(self, dispatcher, tracker, domain):
            # Lấy tin nhắn người dùng để gửi tới OpenFaaS (nếu cần)
            user_message = tracker.latest_message.get("text")  # Ví dụ: "Kết nối OpenFaaS"

            try:
                # Gửi yêu cầu tới hàm OpenFaaS
                response = requests.post(
                    "http://127.0.0.1:8080/function/my-function",  # Địa chỉ hàm OpenFaaS
                    data=user_message  # Nội dung gửi tới OpenFaaS
                )

                # Kiểm tra phản hồi từ OpenFaaS
                if response.status_code == 200:
                    dispatcher.utter_message(text=f"Phản hồi từ OpenFaaS: {response.text}")
                else:
                    dispatcher.utter_message(text="Không thể kết nối tới OpenFaaS. Hãy thử lại sau.")
            except Exception as e:
                dispatcher.utter_message(text=f"Lỗi khi gọi OpenFaaS: {str(e)}")

            return []