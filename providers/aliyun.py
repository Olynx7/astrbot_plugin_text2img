"""阿里云百炼文生图服务提供商"""

from .base import BaseProvider
from .resolutions import get_aliyun_resolutions


class AliyunProvider(BaseProvider):
    """阿里云百炼文生图服务提供商"""

    async def generate_image(self, prompt: str, size: str = "") -> tuple[bytes, str]:
        """生成图片"""
        api_key = self.get_next_api_key()

        # 构建请求体
        payload = {
            "model": self.model,
            "input": {"messages": [{"role": "user", "content": [{"text": prompt}]}]},
            "parameters": {},
        }

        if self.negative_prompt:
            payload["parameters"]["negative_prompt"] = self.negative_prompt
        if size:
            payload["parameters"]["size"] = size
        if "wan" in self.model.lower():
            payload["parameters"]["n"] = 1  # wan系列默认n=4，改为1以节省资源

        session = await self.get_http_session()
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/generation"

        try:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"API调用失败 (HTTP {resp.status}): {error_text}")

                result = await resp.json()
        except Exception as e:
            raise Exception(f"阿里百炼API调用失败: {str(e)}")

        # 解析响应，下载图片
        try:
            image_url = result["output"]["choices"][0]["message"]["content"][0]["image"]
            async with session.get(image_url) as resp:
                if resp.status != 200:
                    raise Exception(f"下载图片失败: HTTP {resp.status}")
                data = await resp.read()
            return data, ".png"
        except (KeyError, IndexError) as e:
            raise Exception(f"解析阿里百炼API响应失败: {str(e)}") from e
        except Exception as e:
            raise Exception(f"阿里百炼API调用失败: {str(e)}") from e

    @staticmethod
    def get_default_base_url() -> str:
        return (
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation"
        )

    def get_supported_ratios(self) -> dict[str, list[str]]:
        """根据模型返回支持的比例和分辨率 (使用 * 号) [小,中,大]"""
        return get_aliyun_resolutions(self.model)
