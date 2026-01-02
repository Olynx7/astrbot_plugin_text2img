"""字节火山引擎文生图服务提供商"""

import base64
from .base import BaseProvider
from .resolutions import get_volcengine_resolutions


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
            "watermark": False,
        }

        session = await self.get_http_session()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
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
            raise Exception(f"解析字节火山API响应失败: {str(e)}") from e
        except Exception as e:
            if "API调用失败" not in str(e):
                raise Exception(f"字节火山API调用失败: {str(e)}") from e
            raise

    @staticmethod
    def get_default_base_url() -> str:
        return "https://ark.cn-beijing.volces.com/api/v3"

    def get_supported_ratios(self) -> dict[str, list[str]]:
        """根据模型返回支持的比例和分辨率 [小,中,大]"""
        return get_volcengine_resolutions(self.model)
