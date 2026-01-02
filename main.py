"""AstrBot 多平台文生图插件

支持 Gitee AI、阿里云百炼、字节火山引擎三大平台。
支持 /t2img 命令调用，支持多种图片比例和多 Key 轮询。
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Optional

import aiofiles

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Image
from astrbot.api.star import Context, Star, StarTools, register

from .providers import BaseProvider, GiteeProvider, AliyunProvider, VolcengineProvider

# 配置常量
DEFAULT_MODEL = "z-image-turbo"
DEFAULT_RATIO = "1:1"
DEFAULT_NEGATIVE_PROMPT = (
    "low quality, bad anatomy, bad hands, text, error, missing fingers, "
    "extra digit, fewer digits, cropped, worst quality, normal quality, "
    "jpeg artifacts, signature, watermark, username, blurry"
)

# 防抖和清理配置
DEBOUNCE_SECONDS = 10.0
MAX_CACHED_IMAGES = 50
OPERATION_CACHE_TTL = 300  # 5分钟清理一次过期操作记录
CLEANUP_INTERVAL = 10  # 每 N 次生成执行一次清理

# Provider 映射
PROVIDER_MAP = {
    "gitee": GiteeProvider,
    "aliyun": AliyunProvider,
    "volcengine": VolcengineProvider,
}


@register(
    "astrbot_plugin_text2img",
    "木有知",
    "多平台文生图插件。支持 Gitee AI、阿里百炼、字节火山。支持 LLM 调用和命令调用，支持多种比例。",
    "2.0",
)
class MultiPlatformText2Image(Star):
    """多平台文生图插件"""

    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.provider_name = config.get("provider", "gitee").lower()

        # 解析 API Keys
        self.api_keys = self._parse_api_keys(config.get("api_key", []))

        # 模型配置
        self.model = config.get("model", DEFAULT_MODEL)
        self.ratio = config.get("ratio", DEFAULT_RATIO)
        self.negative_prompt = config.get("negative_prompt", DEFAULT_NEGATIVE_PROMPT)

        # 创建 provider 实例
        self.provider = self._create_provider()

        # 并发控制
        self.processing_users: set[str] = set()
        self.last_operations: dict[str, float] = {}

        # 图片目录
        self._image_dir: Optional[Path] = None

        # 清理计数器和后台任务引用
        self._generation_count: int = 0
        self._background_tasks: set[asyncio.Task] = set()

    @staticmethod
    def _parse_api_keys(api_keys) -> list[str]:
        """解析 API Keys 配置，支持字符串和列表格式"""
        if isinstance(api_keys, str):
            if api_keys:
                return [k.strip() for k in api_keys.split(",") if k.strip()]
            return []
        elif isinstance(api_keys, list):
            return [str(k).strip() for k in api_keys if str(k).strip()]
        return []

    def _create_provider(self) -> BaseProvider:
        """创建对应的 provider 实例"""
        provider_class = PROVIDER_MAP.get(self.provider_name)
        if not provider_class:
            raise ValueError(f"不支持的provider: {self.provider_name}")

        # 获取 base_url，如果配置中没有，则使用 provider 的默认值
        base_url = self.config.get("base_url") or provider_class.get_default_base_url()

        # 创建 provider 实例
        return provider_class(
            api_keys=self.api_keys,
            base_url=base_url,
            model=self.model,
            negative_prompt=self.negative_prompt,
        )

    def _get_image_dir(self) -> Path:
        """获取图片保存目录（延迟初始化）"""
        if self._image_dir is None:
            base_dir = StarTools.get_data_dir("astrbot_plugin_text2img")
            self._image_dir = base_dir / "images"
            self._image_dir.mkdir(exist_ok=True)
        return self._image_dir

    def _get_save_path(self, extension: str = ".jpg") -> str:
        """生成唯一的图片保存路径"""
        image_dir = self._get_image_dir()
        filename = f"{int(time.time())}_{os.urandom(4).hex()}{extension}"
        return str(image_dir / filename)

    def _sync_cleanup_old_images(self) -> None:
        """同步清理旧图片（在线程池中执行）"""
        try:
            image_dir = self._get_image_dir()
            # 收集所有支持的图片格式
            images: list[Path] = []
            for ext in ("*.jpg", "*.png", "*.webp"):
                images.extend(image_dir.glob(ext))

            # 按修改时间排序
            images.sort(key=lambda p: p.stat().st_mtime)

            if len(images) > MAX_CACHED_IMAGES:
                to_delete = images[: len(images) - MAX_CACHED_IMAGES]
                for img_path in to_delete:
                    try:
                        img_path.unlink()
                    except OSError:
                        pass
        except Exception as e:
            logger.warning(f"清理旧图片时出错: {e}")

    async def _cleanup_old_images(self) -> None:
        """异步清理旧图片，使用线程池执行阻塞操作"""
        await asyncio.to_thread(self._sync_cleanup_old_images)

    def _cleanup_expired_operations(self) -> None:
        """清理过期的操作记录，防止内存泄漏"""
        current_time = time.time()
        expired_keys = [
            key
            for key, timestamp in self.last_operations.items()
            if current_time - timestamp > OPERATION_CACHE_TTL
        ]
        for key in expired_keys:
            del self.last_operations[key]

    def _check_debounce(self, request_id: str) -> bool:
        """检查防抖，返回 True 表示需要拒绝请求"""
        current_time = time.time()

        # 定期清理过期记录
        if len(self.last_operations) > 100:
            self._cleanup_expired_operations()

        if request_id in self.last_operations:
            if current_time - self.last_operations[request_id] < DEBOUNCE_SECONDS:
                return True

        self.last_operations[request_id] = current_time
        return False

    async def _generate_image(
        self, prompt: str, ratio: str = "1:1", quality: str = "m"
    ) -> str:
        """调用文生图 API 生成图片，返回本地文件路径

        Args:
            prompt: 提示词
            ratio: 图片比例 (1:1, 16:9 等)
            quality: 图片质量 (s=低, m=中, h=高)
        """
        try:
            # 获取支持的比例
            supported_ratios = self.provider.get_supported_ratios()
            if ratio not in supported_ratios:
                ratio = self.ratio  # 使用默认比例

            # 根据 quality 选择尺寸 (s=0, m=1, h=2)
            quality_map = {"s": 0, "m": 1, "h": 2}
            quality_index = quality_map.get(quality, 1)  # 默认中等

            size_list = supported_ratios[ratio]
            # 确保索引不越界
            size_index = min(quality_index, len(size_list) - 1)
            target_size = size_list[size_index]

            # 调用 provider 生成图片
            image_data, extension = await self.provider.generate_image(
                prompt, target_size
            )

            # 保存到本地
            filepath = self._get_save_path(extension)
            async with aiofiles.open(filepath, "wb") as f:
                await f.write(image_data)

            # 每 N 次生成执行一次清理
            self._generation_count += 1
            if self._generation_count >= CLEANUP_INTERVAL:
                self._generation_count = 0
                task = asyncio.create_task(self._cleanup_old_images())
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)

            return filepath
        except Exception as e:
            raise Exception(f"生成图片失败: {str(e)}") from e

    @filter.llm_tool(name="draw_image")  # type: ignore
    async def draw(self, event: AstrMessageEvent, prompt: str):
        """根据提示词生成图片。

        Args:
            prompt(string): 图片提示词，需要包含主体、场景、风格等描述
        """
        user_id = event.get_sender_id()
        request_id = user_id

        # 防抖检查
        if self._check_debounce(request_id):
            return "操作太快了，请稍后再试。"

        if request_id in self.processing_users:
            return "您有正在进行的生图任务，请稍候..."

        self.processing_users.add(request_id)
        try:
            image_path = await self._generate_image(prompt, self.ratio, "m")
            await event.send(event.chain_result([Image.fromFileSystem(image_path)]))  # type: ignore
            return f"图片已生成并发送。Prompt: {prompt}"

        except Exception as e:
            logger.error(f"生图失败: {e}")
            return f"生成图片时遇到问题: {str(e)}"
        finally:
            self.processing_users.discard(request_id)

    @filter.command("t2img")
    async def generate_image_command(self, event: AstrMessageEvent):
        """生成图片指令

        用法: /t2img <提示词> [比例] [质量]
        示例: /t2img 一个女孩 9:16 h
        支持比例: 1:1, 4:3, 3:4, 3:2, 2:3, 16:9, 9:16
        质量参数: s (低质量), m (中等), h (高质量)
        """
        message_str = event.message_str  # 获取消息的纯文本内容

        # 移除命令前缀
        content = message_str.strip()
        if content.startswith("t2img"):
            content = content[5:].strip()  # 移除 "t2img "

        if not content:
            yield event.plain_result("请提供提示词！使用方法：/t2img <提示词> [比例] [质量]")
            return
        
        logger.debug(f"收到 /t2img 命令，内容: {content}")

        # 解析参数：从右向左提取可选参数
        parts = content.split()
        prompt = content
        ratio = "1:1"
        quality = "s"

        logger.debug(f"解析参数，初始 parts: {parts}")

        # 支持的比例和质量选项
        supported_ratios = self.provider.get_supported_ratios()
        valid_qualities = {"s", "m", "h"}

        # 尝试提取最后一个参数作为 quality
        if len(parts) > 1 and parts[-1] in valid_qualities:
            quality = parts[-1]
            parts = parts[:-1]
            prompt = " ".join(parts)
            logger.debug(f"提取质量参数: {quality}, 剩余 parts: {parts}, prompt: {prompt}")

        # 尝试提取最后一个参数作为 ratio
        if len(parts) > 1 and parts[-1] in supported_ratios:
            ratio = parts[-1]
            parts = parts[:-1]
            prompt = " ".join(parts)
            logger.debug(f"提取比例参数: {ratio}, 剩余 parts: {parts}, prompt: {prompt}")

        # 如果 prompt 为空
        if not prompt.strip():
            yield event.plain_result("请提供提示词！使用方法：/t2img <提示词> [比例] [质量]")
            return

        user_id = event.get_sender_id()
        request_id = user_id

        # 防抖检查（统一机制）
        if self._check_debounce(request_id):
            yield event.plain_result("操作太快了，请稍后再试。")
            return

        if request_id in self.processing_users:
            yield event.plain_result("您有正在进行的生图任务，请稍候...")
            return

        self.processing_users.add(request_id)

        logger.debug(f"用户 {user_id} 请求生成图片，Prompt: {prompt}, 比例: {ratio}, 质量: {quality}")

        try:
            logger.info(
                f"用户 {user_id} 请求生成图片，Prompt: {prompt}, 比例: {ratio}, 质量: {quality}"
            )
            image_path = await self._generate_image(prompt, ratio, quality)
            yield event.chain_result([Image.fromFileSystem(image_path)])  # type: ignore

        except Exception as e:
            logger.error(f"生图失败: {e}")
            yield event.plain_result(f"生成图片失败: {str(e)}")
        finally:
            self.processing_users.discard(request_id)

    async def close(self) -> None:
        """清理资源"""
        await self.provider.close()
