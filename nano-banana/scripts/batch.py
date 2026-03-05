#!/usr/bin/env python3
"""
Nano Banana 批量生图脚本
用法: 编辑脚本底部的 TASKS 列表，然后运行
      python3 batch.py
"""
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

TASKS = [
    {
        "prompt": """创建一张专业的深色主题特性卡片，用于手机应用 "Minis"。

风格：现代科技 UI 卡片，深黑色背景（#0D1117），简洁无衬线中文字体，蓝紫色渐变强调色，简约优雅。类似 Apple 产品营销或 Linear 设计美学。3:4 竖版格式。

卡片内容（必须用中文显示）：
- 顶部大图标：🐧
- 主标题（大号粗体）：纯本地 Linux 环境
- 副标题：完整 Alpine Linux 内置于 App
- 特性列表：
  ✦ 90%+ 常用软件完美运行
  ✦ Python · FFmpeg · git · curl 开箱即用
  ✦ 数据永不离开你的手机
- 右下角品牌标识：Minis

视觉细节：背景隐约可见终端代码行或绿色矩阵光点，发光强调线条，高级质感。不要出现人物照片。""",
        "file": "/var/minis/attachments/minis_card1_linux_cn.png",
        "aspect": "3:4",
        "size": "2K",
    },
    {
        "prompt": """创建一张专业的深色主题特性卡片，用于手机应用 "Minis"。

风格：现代科技 UI 卡片，深黑色背景（#0D1117），简洁无衬线中文字体，金橙色渐变强调色，简约优雅。类似 Apple 产品营销或 Linear 设计美学。3:4 竖版格式。

卡片内容（必须用中文显示）：
- 顶部大图标：🔑
- 主标题（大号粗体）：多 AI 自由接入
- 副标题：带上自己的 API Key 或订阅即可
- 以发光胶囊标签展示各 AI 提供商：
  Claude · GPT · Gemini · Ollama
- 特性列表：
  ✦ 无需注册任何新账号
  ✦ 随时切换模型
  ✦ 一个 App 统一管理所有 AI
- 右下角品牌标识：Minis

视觉细节：背景隐约可见网络节点连线，各 AI 提供商以发光胶囊标签展示，高级深色卡片质感。""",
        "file": "/var/minis/attachments/minis_card2_ai_cn.png",
        "aspect": "3:4",
        "size": "2K",
    },
    {
        "prompt": """创建一张专业的深色主题特性卡片，用于手机应用 "Minis"。

风格：现代科技 UI 卡片，深黑色背景（#0D1117），简洁无衬线中文字体，青绿色渐变强调色，简约优雅。类似 Apple 产品营销或 Linear 设计美学。3:4 竖版格式。

卡片内容（必须用中文显示）：
- 顶部大图标：📱
- 主标题（大号粗体）：与手机无缝连接
- 副标题：AI 直接调用 iPhone 原生系统能力
- 图标网格展示功能（emoji + 中文标签）：
  🏥 健康数据   📅 日历
  📍 位置       📸 相册
  🌤 天气       🔊 语音
- 底部说明：无需云端中转，全部本地原生调用
- 右下角品牌标识：Minis

视觉细节：背景隐约可见 iPhone 轮廓，发光连线向外辐射至各功能图标，高级质感。""",
        "file": "/var/minis/attachments/minis_card3_device_cn.png",
        "aspect": "3:4",
        "size": "2K",
    },
    {
        "prompt": """创建一张专业的深色主题特性卡片，用于手机应用 "Minis"。

风格：现代科技 UI 卡片，深黑色背景（#0D1117），简洁无衬线中文字体，紫罗兰色渐变强调色，简约优雅。类似 Apple 产品营销或 Linear 设计美学。3:4 竖版格式。

卡片内容（必须用中文显示）：
- 顶部大图标：🌐
- 主标题（大号粗体）：内置本地浏览器
- 副标题：AI 自主浏览网页、提取内容、完成操作
- 特性列表：
  ✦ 全程本地执行，无需云端中转
  ✦ AI 像人一样操控网页
  ✦ 提取内容、填写表单、自动导航
- 分割线后展示第二特性：
  ⚡ 零安装零配置 — 首次启动自动部署，即开即用
- 右下角品牌标识：Minis

视觉细节：背景隐约可见浏览器线框，光标点击波纹效果，发光紫色强调线条。""",
        "file": "/var/minis/attachments/minis_card4_browser_cn.png",
        "aspect": "3:4",
        "size": "2K",
    },
]

for i, task in enumerate(TASKS):
    print(f"[{i+1}/{len(TASKS)}] Generating: {task['file']}")
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[task["prompt"]],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio=task.get("aspect", "1:1"),
                    image_size=task.get("size", "1K"),
                ),
            ),
        )
        saved = False
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                part.as_image().save(task["file"])
                print(f"  ✅ Saved: {task['file']}")
                saved = True
            elif hasattr(part, "text") and part.text:
                print(f"  ℹ️  {part.text}")
        if not saved:
            print(f"  ❌ No image returned for task {i+1}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

print("\nAll done!")
