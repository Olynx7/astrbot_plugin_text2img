"""文生图服务提供商基类"""

from abc import ABC, abstractmethod
from typing import Optional
import aiohttp


class BaseProvider(ABC):
    """文生图服务提供商基类"""
    
    def __init__(self, api_keys: list[str], base_url: str, model: str, 
                 negative_prompt: str = "", **kwargs):
        """初始化提供商
        
        Args:
            api_keys: API Key 列表
            base_url: API 基础 URL
            model: 模型名称
            negative_prompt: 负面提示词
            **kwargs: 其他平台特定参数
        """
        self.api_keys = api_keys
        self.base_url = base_url
        self.model = model
        self.negative_prompt = negative_prompt
        self.current_key_index = 0
        self._http_session: Optional[aiohttp.ClientSession] = None
        
    def get_next_api_key(self) -> str:
        """轮询获取下一个 API Key"""
        if not self.api_keys:
            raise ValueError("请先配置 API Key")
        
        api_key = self.api_keys[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        return api_key
    
    async def get_http_session(self) -> aiohttp.ClientSession:
        """获取复用的 HTTP Session"""
        if self._http_session is None or self._http_session.closed:
            self._http_session = aiohttp.ClientSession()
        return self._http_session
    
    @abstractmethod
    async def generate_image(self, prompt: str, size: str = "") -> tuple[bytes, str]:
        """生成图片
        
        Args:
            prompt: 提示词
            size: 图片尺寸，为空则使用默认尺寸
            
        Returns:
            tuple[bytes, str]: (图片数据, 文件扩展名如 ".jpg")
        """
        pass
    
    async def close(self):
        """关闭连接"""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
    
    @staticmethod
    @abstractmethod
    def get_default_base_url() -> str:
        """获取默认的 base_url"""
        pass
    
    @staticmethod
    @abstractmethod
    def get_supported_ratios() -> dict[str, list[str]]:
        """获取支持的图片比例
        
        Returns:
            dict[str, list[str]]: 比例到尺寸列表的映射
        """
        pass
