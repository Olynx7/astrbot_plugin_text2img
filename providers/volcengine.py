"""字节火山引擎文生图服务提供商"""

import base64
from .base import BaseProvider


class VolcengineProvider(BaseProvider):
    """字节火山引擎文生图服务提供商"""
    
    async def generate_image(self, prompt: str, size: str = "") -> tuple[bytes, str]:
        """生成图片"""
        api_key = self.get_next_api_key()
        
        # 构建请求体
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "watermark": False
        }
        
        session = await self.get_http_session()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/images/generations"
        
        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"API调用失败 (HTTP {resp.status}): {error_text}")
                
                result = await resp.json()
        except Exception as e:
            raise Exception(f"字节火山API调用失败: {str(e)}")
        
        # 解析响应
        try:
            if "data" in result and len(result["data"]) > 0:
                data_item = result["data"][0]
                if "url" in data_item:
                    # 下载图片
                    async with session.get(data_item["url"]) as resp:
                        if resp.status != 200:
                            raise Exception(f"下载图片失败: HTTP {resp.status}")
                        data = await resp.read()
                    return data, ".jpg"
                elif "b64_json" in data_item:
                    data = base64.b64decode(data_item["b64_json"])
                    return data, ".jpg"
                else:
                    raise Exception("响应中未找到图片URL或Base64数据")
            else:
                raise Exception("响应中未找到图片数据")
        except (KeyError, IndexError) as e:
            raise Exception(f"解析字节火山API响应失败: {str(e)}")
    
    @staticmethod
    def get_default_base_url() -> str:
        return "https://ark.cn-beijing.volces.com/api/v3"
    
    def get_supported_ratios(self) -> dict[str, list[str]]:
        """根据模型返回支持的比例和分辨率 [小,中,大]"""
        model_lower = self.model.lower()
        
        # Seedream 4.5
        if "4-5" in model_lower or "4.5" in model_lower:
            return {
                "1:1": ["1600x1600", "2048x2048", "2560x2560"],
                "4:3": ["1792x1344", "2304x1728", "2816x2112"],
                "3:4": ["1344x1792", "1728x2304", "2112x2816"],
                "3:2": ["1920x1280", "2496x1664", "3072x2048"],
                "2:3": ["1280x1920", "1664x2496", "2048x3072"],
                "16:9": ["2048x1152", "2560x1440", "3200x1800"],
                "9:16": ["1152x2048", "1440x2560", "1800x3200"],
            }
        
        # Seedream 4.0
        elif "4-0" in model_lower or "4.0" in model_lower:
            return {
                "1:1": ["1280x1280", "2048x2048", "2560x2560"],
                "4:3": ["1440x1080", "2304x1728", "2816x2112"],
                "3:4": ["1080x1440", "1728x2304", "2112x2816"],
                "3:2": ["1536x1024", "2496x1664", "3072x2048"],
                "2:3": ["1024x1536", "1664x2496", "2048x3072"],
                "16:9": ["1920x1080", "2560x1440", "3200x1800"],
                "9:16": ["1080x1920", "1440x2560", "1800x3200"],
            }
        
        # Seedream 3.0
        elif "3-0" in model_lower or "3.0" in model_lower:
            return {
                "1:1": ["512x512", "1024x1024", "2048x2048"],
                "4:3": ["640x480", "1280x960", "2048x1536"],
                "3:4": ["480x640", "960x1280", "1536x2048"],
                "3:2": ["768x512", "1536x1024", "2048x1360"],
                "2:3": ["512x768", "1024x1536", "1360x2048"],
                "16:9": ["640x360", "1280x720", "1920x1080"],
                "9:16": ["360x640", "720x1280", "1080x1920"],
            }
        
        # 默认使用4.5配置
        else:
            return {
                "1:1": ["1600x1600", "2048x2048", "2560x2560"],
                "4:3": ["1792x1344", "2304x1728", "2816x2112"],
                "3:4": ["1344x1792", "1728x2304", "2112x2816"],
                "3:2": ["1920x1280", "2496x1664", "3072x2048"],
                "2:3": ["1280x1920", "1664x2496", "2048x3072"],
                "16:9": ["2048x1152", "2560x1440", "3200x1800"],
                "9:16": ["1152x2048", "1440x2560", "1800x3200"],
            }
