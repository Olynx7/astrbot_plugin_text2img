"""Gitee AI 文生图服务提供商"""

import base64
from typing import Optional
from openai import AsyncOpenAI, AuthenticationError, RateLimitError, APIError
from .base import BaseProvider
from .resolutions import get_gitee_resolutions


class GiteeProvider(BaseProvider):
    """Gitee AI 文生图服务提供商"""

    def __init__(
        self,
        api_keys: list[str],
        base_url: str,
        model: str,
        negative_prompt: str = "",
        **kwargs,
    ):
        super().__init__(api_keys, base_url, model, negative_prompt, **kwargs)
        self._openai_clients: dict[str, AsyncOpenAI] = {}

    def _get_client(self) -> AsyncOpenAI:
        """获取复用的 AsyncOpenAI 客户端"""
        api_key = self.get_next_api_key()

        if api_key not in self._openai_clients:
            self._openai_clients[api_key] = AsyncOpenAI(
                base_url=self.base_url,
                api_key=api_key,
            )

        return self._openai_clients[api_key]

    async def generate_image(self, prompt: str, size: str = "") -> tuple[bytes, str]:
        """生成图片"""
        client = self._get_client()

        # 构建请求参数
        kwargs = {
            "prompt": prompt,
            "model": self.model,
            "size": size,
        }

        if self.negative_prompt:
            kwargs["extra_body"] = {"negative_prompt": self.negative_prompt}

        try:
            response = await client.images.generate(**kwargs)  # type: ignore
        except AuthenticationError as e:
            raise Exception("API Key 无效或已过期，请检查配置。") from e
        except RateLimitError as e:
            raise Exception("API 调用次数超限或并发过高，请稍后再试。") from e
        except APIError as e:
            if e.status_code and e.status_code >= 500:
                raise Exception("Gitee AI 服务器内部错误，请稍后再试。") from e
            raise Exception(f"API调用失败: {str(e)}") from e
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}") from e

        if not response.data:  # type: ignore
            raise Exception("生成图片失败：未返回数据")

        image_data = response.data[0]  # type: ignore

        # 下载图片数据
        if image_data.url:
            session = await self.get_http_session()
            async with session.get(image_data.url) as resp:
                if resp.status != 200:
                    raise Exception(f"下载图片失败: HTTP {resp.status}")
                data = await resp.read()
            return data, ".jpg"
        elif image_data.b64_json:
            data = base64.b64decode(image_data.b64_json)
            return data, ".jpg"
        else:
            raise Exception("生成图片失败：未返回 URL 或 Base64 数据")

    async def close(self):
        """关闭连接"""
        await super().close()
        for client in self._openai_clients.values():
            await client.close()
        self._openai_clients.clear()

    @staticmethod
    def get_default_base_url() -> str:
        return "https://ai.gitee.com/v1"

    def get_supported_ratios(self) -> dict[str, list[str]]:
        """返回支持的比例和对应的尺寸列表 [小,中,大]"""
        return get_gitee_resolutions(self.model)
