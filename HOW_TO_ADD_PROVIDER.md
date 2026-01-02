# 如何添加新的文生图服务提供商

## 步骤

### 1. 创建新的 Provider 类

在 `providers/` 目录下创建新文件，例如 `openai.py`：

```python
"""OpenAI DALL-E 文生图服务提供商"""

from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI DALL-E 文生图服务提供商"""
    
    async def generate_image(self, prompt: str, size: str = "") -> tuple[bytes, str]:
        """生成图片
        
        Args:
            prompt: 提示词
            size: 图片尺寸
            
        Returns:
            tuple[bytes, str]: (图片数据, 文件扩展名)
        """
        api_key = self.get_next_api_key()
        target_size = size if size else self.default_size
        
        # 实现你的 API 调用逻辑
        # ...
        
        # 返回图片数据和扩展名
        return image_bytes, ".png"
    
    @staticmethod
    def get_default_base_url() -> str:
        """返回默认的 API 地址"""
        return "https://api.openai.com/v1"
    
    def get_supported_ratios(self) -> dict[str, list[str]]:
        """返回支持的图片比例和分辨率 [小,中,大]
        
        注意：这是实例方法，可以根据 self.model 返回不同的分辨率
        """
        return {
            "1:1": ["512x512", "1024x1024", "2048x2048"],
            "16:9": ["1280x720", "1792x1024", "2560x1440"],
            "9:16": ["720x1280", "1024x1792", "1440x2560"],
        }
```

### 2. 注册到 __init__.py

在 `providers/__init__.py` 中添加导入：

```python
from .openai import OpenAIProvider

__all__ = [..., "OpenAIProvider"]
```

### 3. 注册到 main.py

在 `main.py` 的 `PROVIDER_MAP` 中添加：

```python
PROVIDER_MAP = {
    "gitee": GiteeProvider,
    "aliyun": AliyunProvider,
    "volcengine": VolcengineProvider,
    "openai": OpenAIProvider,  # 新增
}
```

### 4. 更新配置 schema

在 `_conf_schema.json` 中更新 provider 的 enum：

```json
{
    "provider": {
        "enum": ["gitee", "aliyun", "volcengine", "openai"]
    }
}
```

### 5. 测试

配置新的 provider：

```json
{
  "provider": "openai",
  "api_key": ["your-openai-api-key"],
  "model": "dall-e-3"
}
```

## BaseProvider 接口说明

必须实现的方法：

### `async def generate_image(prompt: str, size: str = "") -> tuple[bytes, str]`
生成图片，返回 (图片字节数据, 文件扩展名)

### `@staticmethod def get_default_base_url() -> str`
返回默认的 API Base URL

### `@staticmethod def get_supported_ratios() -> dict[str, list[str]]`
返回支持的图片比例映射，格式如：
```python
{
    "1:1": ["1024x1024", "2048x2048"],
    "16:9": ["1920x1080"],
}
```

## 可用的基类方法

- `get_next_api_key()`: 轮询获取下一个 API Key
- `get_http_session()`: 获取复用的 aiohttp Session
- `close()`: 关闭连接（可选重写）

## 可用的属性

- `self.api_keys`: API Key 列表
- `self.base_url`: API Base URL
- `self.model`: 模型名称
- `self.default_size`: 默认图片尺寸
- `self.negative_prompt`: 负面提示词

## 完整示例

参考现有的实现：
- `providers/gitee.py` - 使用 OpenAI SDK
- `providers/aliyun.py` - 使用原生 HTTP 请求
- `providers/volcengine.py` - 处理多种响应格式
