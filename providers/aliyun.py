"""阿里云百炼文生图服务提供商"""

from .base import BaseProvider


class AliyunProvider(BaseProvider):
    """阿里云百炼文生图服务提供商"""
    
    async def generate_image(self, prompt: str, size: str = "") -> tuple[bytes, str]:
        """生成图片"""
        api_key = self.get_next_api_key()
        
        # 构建请求体
        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {}
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
            "Content-Type": "application/json"
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
            raise Exception(f"解析阿里百炼API响应失败: {str(e)}")
    
    @staticmethod
    def get_default_base_url() -> str:
        return "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation"
    
    def get_supported_ratios(self) -> dict[str, list[str]]:
        """根据模型返回支持的比例和分辨率 (使用 * 号) [小,中,大]"""
        model_lower = self.model.lower()
        
        # Qwen-Image系列
        if "qwen-image" in model_lower:
            return {
                "1:1": ["1024*1024", "1328*1328", "1328*1328"],
                "4:3": ["1152*864", "1472*1104", "1472*1104"],
                "3:4": ["864*1152", "1104*1472", "1104*1472"],
                "16:9": ["1280*720", "1664*928", "1664*928"],
                "9:16": ["720*1280", "928*1664", "928*1664"],
            }
        
        # Z-Image-turbo系列
        elif "z-image-turbo" in model_lower:
            return {
                "1:1": ["1024*1024", "1280*1280", "1536*1536"],
                "2:3": ["832*1248", "1024*1536", "1248*1872"],
                "3:2": ["1248*832", "1536*1024", "1872*1248"],
                "3:4": ["864*1152", "1104*1472", "1296*1728"],
                "4:3": ["1152*864", "1472*1104", "1728*1296"],
                "7:9": ["896*1152", "1120*1440", "1344*1728"],
                "9:7": ["1152*896", "1440*1120", "1728*1344"],
                "9:16": ["720*1280", "864*1536", "1152*2048"],
                "16:9": ["1280*720", "1536*864", "2048*1152"],
                "9:21": ["576*1344", "720*1680", "864*2016"],
                "21:9": ["1344*576", "1680*720", "2016*864"],
            }
        
        # wan2.6系列
        elif "wan" in model_lower:
            return {
                "1:1": ["1024*1024", "1280*1280", "1440*1440"],
                "3:4": ["960*1280", "1104*1472", "1104*1472"],
                "4:3": ["1280*960", "1472*1104", "1472*1104"],
                "9:16": ["768*1360", "960*1696", "960*1696"],
                "16:9": ["1360*768", "1696*960", "1696*960"],
            }
        
        # 默认通用分辨率
        else:
            return {
                "1:1": ["768*768", "1024*1024", "1328*1328"],
                "4:3": ["896*672", "1152*864", "1472*1104"],
                "3:4": ["672*896", "864*1152", "1104*1472"],
                "3:2": ["768*512", "1536*1024", "2304*1536"],
                "2:3": ["512*768", "1024*1536", "1536*2304"],
                "16:9": ["1280*720", "1920*1080", "2560*1440"],
                "9:16": ["720*1280", "1080*1920", "1440*2560"],
            }
