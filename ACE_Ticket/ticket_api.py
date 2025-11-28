import httpx
import logging
import json
from typing import List, Dict, Optional, Any

# 配置日志
logger = logging.getLogger(__name__)

class TicketAPI:
    """Ticket系统API客户端"""
    
    def __init__(self, api_key: str = "5a20d885-455d-4801-9e31-1e9196c13367", base_url: str = "https://unisticket.item.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    async def fetch_ticket_list(self, 
                              page: int = 1, 
                              size: int = 10, 
                              display_status_ids: Optional[List[int]] = None,
                              staff_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取Ticket列表
        
        Args:
            page: 页码
            size: 每页数量
            display_status_ids: 状态ID列表 (例如 [2] 代表已解决)
            staff_ids: 员工ID列表
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}/api/item-tickets/v1/iam/tickets/page"
        
        payload = {
            "size": size,
            "page": page,
            "input": {}
        }
        
        if display_status_ids:
            payload["input"]["displayStatusIds"] = display_status_ids
            
        if staff_ids:
            payload["input"]["staffIds"] = staff_ids
            
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Requesting Ticket List: {url}")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch ticket list: {str(e)}")
            raise

    async def fetch_ticket_messages(self, 
                                  ticket_id: str,
                                  page: int = 1,
                                  size: int = 10,
                                  msg_types: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        获取Ticket消息列表
        
        Args:
            ticket_id: Ticket ID
            page: 页码
            size: 每页数量
            msg_types: 消息类型列表 (1:邮件消息, 3:内部消息, 5:公开回复)
            
        Returns:
            API响应数据
        """
        url = f"{self.base_url}/api/item-tickets/v1/iam/tickets/{ticket_id}/messages"
        
        payload = {
            "size": size,
            "page": page,
            "orders": [
                {
                    "column": "id",
                    "asc": False
                }
            ],
            "input": {}
        }
        
        if msg_types:
            payload["input"]["types"] = msg_types
            
        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Requesting Ticket Messages: {url}")
                response = await client.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch ticket messages: {str(e)}")
            raise

# 用于快速测试
if __name__ == "__main__":
    import asyncio
    
    async def test():
        logging.basicConfig(level=logging.INFO)
        api = TicketAPI()
        
        try:
            # 1. 获取列表
            print("\n=== Testing Fetch Ticket List ===")
            tickets = await api.fetch_ticket_list(size=2, display_status_ids=[2])
            print(json.dumps(tickets, indent=2, ensure_ascii=False))
            
            if tickets.get("code") == 200 and tickets.get("data", {}).get("records"):
                first_ticket_id = tickets["data"]["records"][0]["id"]
                
                # 2. 获取消息
                print(f"\n=== Testing Fetch Messages for Ticket {first_ticket_id} ===")
                messages = await api.fetch_ticket_messages(
                    ticket_id=first_ticket_id,
                    msg_types=[1, 5]
                )
                print(json.dumps(messages, indent=2, ensure_ascii=False))
                
        except Exception as e:
            print(f"Error: {e}")

    asyncio.run(test())

