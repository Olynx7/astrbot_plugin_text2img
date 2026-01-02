# AstrBot 多平台文生图插件

<div align="center">

![Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

一个强大的 AstrBot 文生图插件，支持多平台 AI 绘图服务

[功能特性](#功能特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [配置说明](#配置说明)

</div>

---

## 功能特性

### 🎨 多平台支持
- **Gitee AI** - 免费额度，适合个人使用
- **阿里云百炼** - 高质量输出，支持多种模型
- **字节火山引擎** - 专业级服务，高分辨率

### 🚀 智能体验
- ✨ **比例 + 质量参数**: 无需记忆复杂分辨率，使用 `1:1`、`16:9` 等比例 + `s/m/h` 质量即可
- 🧠 **模型自适应**: 根据选择的模型自动适配最佳分辨率配置
- 📝 **命令调用**: 简单的 `/t2i` 命令

### 🔧 开发友好
- 📦 **Provider 架构**: 模块化设计，易于扩展新平台
- 🔄 **多 Key 轮询**: 支持配置多个 API Key 自动轮换
- 🧹 **自动清理**: 智能管理缓存，节省存储空间
- ⚙️ **灵活配置**: 支持自定义负面提示词等高级参数

---

## 快速开始

### 安装

将插件放置到 AstrBot 的 `plugins` 目录下即可自动加载。

### 获取 API Key

选择一个平台并获取 API Key：

<details>
<summary><b>Gitee AI</b> (推荐新手，有免费额度)</summary>

1. 访问 [Gitee AI Serverless API](https://ai.gitee.com/serverless-api?model=z-image-turbo)
2. 注册/登录账号
3. 获取 API Key
4. 推荐模型: `z-image-turbo`

</details>

<details>
<summary><b>阿里云百炼</b> (高质量，多模型选择)</summary>

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 开通服务并获取 API Key
3. 推荐模型: 
   - `qwen-image-max` - 通义千问高质量模型
   - `z-image-turbo` - 快速生成
   - `wan2.6-t2i` - 万相 2.6

</details>

<details>
<summary><b>字节火山方舟</b> (专业级，高分辨率)</summary>

1. 访问 [火山方舟](https://console.volcengine.com/ark/)
2. 开通服务并获取 API Key
3. 推荐模型:
   - `doubao-seedream-4-5` - SeeDream 4.5 (最新)
   - `doubao-seedream-4-0` - SeeDream 4.0
   - `doubao-seedream-3-0` - SeeDream 3.0

</details>

### 基础配置

在 AstrBot 配置面板中配置插件（最简配置）：

```json
{
  "provider": "gitee",
  "api_key": ["your-api-key-here"],
  "model": "z-image-turbo"
}
```

### 开始使用

```bash
/t2i 一只可爱的橘猫
/t2i 赛博朋克城市 16:9 h
```

---

## 使用指南

### 命令列表

| 命令 | 格式 | 说明 | 示例 |
|------|------|------|------|
| `/t2i` | `/t2i <提示词>` | 使用默认配置生成图片 | `/t2i 日落风景` |
| `/t2i` | `/t2i <提示词> [比例] [质量]` | 指定比例和质量生成 | `/t2i 猫咪 16:9 h` |

### 比例参数

| 比例 | 说明 | 适用场景 |
|------|------|----------|
| `1:1` | 正方形 | 头像、Logo、社交媒体 |
| `4:3` | 传统屏幕 | 演示文稿、照片打印 |
| `3:4` | 竖版 | 手机壁纸、海报 |
| `16:9` | 宽屏 | 桌面壁纸、视频封面 |
| `9:16` | 竖屏视频 | 短视频、Stories |

### 质量参数

| 参数 | 说明 | 分辨率级别 |
|------|------|-----------|
| `s` | Small - 小尺寸（默认） | 快速生成，文件小 |
| `m` | Medium - 中尺寸 | 平衡质量和速度 |
| `h` | High - 大尺寸 | 高质量，细节丰富 |

---

## 配置说明

### 配置参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `provider` | string | 服务提供商 | `gitee` |
| `api_key` | array | API Key 列表（支持多个） | `[]` |
| `model` | string | 模型名称 | `z-image-turbo` |
| `ratio` | string | 默认图片比例 | `1:1` |
| `negative_prompt` | string | 负面提示词（可选） | `""` |


## 开发者指南

想要添加新平台？查看 [HOW_TO_ADD_PROVIDER.md](HOW_TO_ADD_PROVIDER.md)

### 核心特性

- **模型自适应**: 不同模型自动返回对应的最佳分辨率配置
- **质量映射**: `s/m/h` 自动映射到分辨率列表索引
- **异步架构**: 全异步实现，高性能
- **防抖机制**: 避免重复请求
- **自动清理**: 智能管理缓存图片

---

## 致谢

感谢原作者 **[木有知](https://github.com/muyouzhi6/astrbot_plugin_gitee_aiimg)** 开发的初始版本，本插件在其基础上进行了重构和扩展。

## 开发路线图

### 🚧 计划中的功能

- 🤖 **LLM 工具调用**: 支持通过自然语言让 AI 助手生成图片（即将推出）
- 🌐 **更多平台支持**: 
  - OpenAI DALL-E
  - Stability AI
  - Midjourney (如果开放 API)
  - 更多国内平台
- 🎛️ **高级参数**: 支持更多模型特定参数
- 📊 **批量生成**: 一次生成多张图片
- 🎨 **图生图**: 支持基于参考图生成

欢迎在 [Issues](https://github.com/Olynx7/astrbot_plugin_text2img/issues) 提出功能建议！

---

## 更新日志

### v1.0 (2026-01-02)

- ✨ 全新的比例 + 质量参数系统
- 🧠 模型自适应分辨率配置
- 🏗️ Provider 架构重构
- 📦 支持阿里云多模型、字节火山多版本
- 🔧 简化用户体验

---

## 许可证

MIT License







