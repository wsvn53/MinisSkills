---
name: nano-banana
description: 使用 Google Nano Banana（Gemini 图像生成 API）生成或编辑图片。当用户说"生成图片"、"画一张"、"帮我做张图"、"图片编辑"、"把这张图改成"、"nano banana"、"nanobanana"、"香蕉"图像生成相关需求时，自动触发此 skill。即使用户没有明确提到 Nano Banana，只要涉及 AI 图片生成或编辑，也应主动使用此 skill。
---

# Nano Banana 图片生成 Skill

基于 Google Gemini 图像生成 API（即 Nano Banana），在本地用 Python 生成或编辑图片。

## 快速流程

1. 检查环境（API Key + 依赖）
2. 根据需求选择模式（文生图 / 图片编辑 / 多图混合）
3. 选择合适的模型
4. **直接使用 skill 内置脚本**，无需重新编写
5. 运行脚本，保存结果到 `/var/minis/attachments/`
6. 在对话中内联展示图片

---

## 环境准备

### 检查 API Key
```bash
source /etc/profile && echo $GEMINI_API_KEY | head -c 10
```

> ⚠️ **必须用 `source /etc/profile`**，否则环境变量不生效。Key 存储在 `/etc/profile` 中的 `GEMINI_API_KEY`。

如未设置，引导用户在 [Google AI Studio](https://aistudio.google.com/apikey) 获取，然后：
```bash
echo 'export GEMINI_API_KEY="your_key_here"' >> /etc/profile
```

### 检查依赖
```bash
pip show google-genai pillow 2>&1 | grep -E "^Name|not found"
```

如未安装：
```bash
pip install google-genai pillow
```

---

## 模型选择

| 模型 | 模型 ID | 适用场景 |
|------|---------|---------|
| **Nano Banana 2**（推荐首选） | `gemini-3.1-flash-image-preview` | 速度快、质量好、支持 2K，日常首选 |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | 专业资产、复杂指令、高保真文字渲染 |
| **Nano Banana（原版）** | `gemini-2.5-flash-image` | 极速低延迟，简单任务 |

**默认使用 `gemini-3.1-flash-image-preview`**，除非用户明确要求其他版本。

---

## ⚠️ 已知 API 陷阱（必读）

### 1. 宽高比 / 分辨率配置

❌ **错误写法**（旧版，会报 `AttributeError`）：
```python
# types.ImageGenerationConfig 不存在！
image_generation_config=types.ImageGenerationConfig(aspect_ratio="16:9")
```

✅ **正确写法**：
```python
# 使用 image_config=types.ImageConfig(...)
config=types.GenerateContentConfig(
    response_modalities=["IMAGE"],
    image_config=types.ImageConfig(
        aspect_ratio="16:9",  # 可选: 1:1, 4:3, 3:4, 16:9, 9:16
        image_size="2K",      # 可选: 1K, 2K（默认 1K）
    ),
)
```

### 2. 环境变量加载

❌ 直接 `python3 script.py` 可能读不到 Key  
✅ 始终用 `source /etc/profile && python3 script.py`

### 3. 图片保存

使用 `part.as_image()` 返回 PIL Image 对象，直接 `.save(path)` 即可。无需手动处理 base64。

---

## 内置脚本

> 直接复制使用，无需重新编写。所有脚本运行方式：
> ```bash
> source /etc/profile && python3 <skill-path>/nano-banana/scripts/<script>.py [args]
> ```

---

### 📄 `gen.py` — 文生图（主力脚本）

```python
#!/usr/bin/env python3
"""
Nano Banana 文生图脚本
用法: python3 gen.py "prompt内容" [输出路径] [宽高比] [分辨率]
示例: python3 gen.py "一只熊猫在竹林喝茶" /var/minis/attachments/out.png 1:1 2K
"""
import os, sys
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

prompt      = sys.argv[1] if len(sys.argv) > 1 else "a beautiful landscape"
output_path = sys.argv[2] if len(sys.argv) > 2 else "/var/minis/attachments/output.png"
aspect      = sys.argv[3] if len(sys.argv) > 3 else "1:1"
size        = sys.argv[4] if len(sys.argv) > 4 else "1K"

print(f"Generating: {prompt[:60]}...")
print(f"Output: {output_path} | {aspect} | {size}")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[prompt],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio=aspect,
            image_size=size,
        ),
    ),
)

saved = False
for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        part.as_image().save(output_path)
        print(f"✅ Saved: {output_path}")
        saved = True
    elif hasattr(part, "text") and part.text:
        print(f"ℹ️  Model: {part.text}")

if not saved:
    print("❌ No image returned. Try rephrasing the prompt.")
    sys.exit(1)
```

---

### 📄 `edit.py` — 图片编辑（图 + 文 → 图）

```python
#!/usr/bin/env python3
"""
Nano Banana 图片编辑脚本
用法: python3 edit.py <输入图片路径> "编辑指令" [输出路径]
示例: python3 edit.py /var/minis/attachments/photo.jpg "给猫加一顶巫师帽" /var/minis/attachments/edited.png
"""
import os, sys, base64
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

if len(sys.argv) < 3:
    print("Usage: edit.py <input_image> <prompt> [output_path]")
    sys.exit(1)

input_path  = sys.argv[1]
edit_prompt = sys.argv[2]
output_path = sys.argv[3] if len(sys.argv) > 3 else "/var/minis/attachments/edited.png"

ext = input_path.lower().rsplit(".", 1)[-1]
mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
mime_type = mime_map.get(ext, "image/jpeg")

with open(input_path, "rb") as f:
    image_bytes = f.read()

print(f"Editing: {input_path}")
print(f"Instruction: {edit_prompt[:60]}...")

response = client.models.generate_content(
    model="gemini-3.1-flash-image-preview",
    contents=[
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        edit_prompt,
    ],
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE", "TEXT"],
    ),
)

for part in response.candidates[0].content.parts:
    if part.inline_data is not None:
        part.as_image().save(output_path)
        print(f"✅ Saved: {output_path}")
    elif hasattr(part, "text") and part.text:
        print(f"ℹ️  Model: {part.text}")
```

---

### 📄 `batch.py` — 批量生图（多 prompt → 多图）

```python
#!/usr/bin/env python3
"""
Nano Banana 批量生图脚本
用法: python3 batch.py  (直接编辑脚本底部的 TASKS 列表)
"""
import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# ✏️ 编辑此处定义批量任务
TASKS = [
    {"prompt": "a futuristic city at night", "file": "/var/minis/attachments/batch_1.png", "aspect": "16:9"},
    {"prompt": "a cozy coffee shop interior", "file": "/var/minis/attachments/batch_2.png", "aspect": "1:1"},
]

for i, task in enumerate(TASKS):
    print(f"[{i+1}/{len(TASKS)}] {task['file']}")
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
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            part.as_image().save(task["file"])
            print(f"  ✅ Saved")
        elif hasattr(part, "text") and part.text:
            print(f"  ℹ️  {part.text}")

print("All done!")
```

---

## 实际操作步骤

当用户发出图片生成请求时：

1. **理解需求** — 判断是文生图、图片编辑还是批量生图
2. **检查 API Key** — `source /etc/profile && echo $GEMINI_API_KEY | head -c 10`
3. **检查脚本是否存在** — `ls <skill-path>/nano-banana/scripts/`
4. **若脚本不存在**，用 `file_write` 将上方对应脚本写入 skill 目录
5. **执行**：
   - 文生图：`source /etc/profile && python3 <skill-path>/nano-banana/scripts/gen.py "prompt" /var/minis/attachments/out.png 16:9 2K`
   - 图片编辑：`source /etc/profile && python3 <skill-path>/nano-banana/scripts/edit.py <图片路径> "指令" /var/minis/attachments/out.png`
   - 批量：编辑 `scripts/batch.py` 中的 TASKS，再运行
6. **展示结果** — `![描述](minis://attachments/out.png)`

---

## Prompt 写作技巧

- **写场景描述，不要堆关键词** — "一位老年日本陶艺家在工作室专注拉坯，窗外透进柔和午后阳光，照片级写实风格" 优于 "日本 陶艺 老人 写实"
- **明确风格** — 摄影风格加相机参数（"50mm 定焦镜头，浅景深"）；插画风格说明画风（"吉卜力风格水彩"）
- **图中文字** — 明确说明要显示的文字内容，文字渲染效果更好
- **迭代修改** — 用 `edit.py` 在已有图上小幅调整，比重新生成效率更高
- **宽高比选择** — 社交媒体配图用 `16:9`，头像/封面用 `1:1`，手机壁纸用 `9:16`

---

## 常见问题

| 问题 | 原因 & 解决方案 |
|------|----------------|
| `AttributeError: ImageGenerationConfig` | 旧写法已废弃，改用 `image_config=types.ImageConfig(...)` |
| `KeyError: GEMINI_API_KEY` | 先执行 `source /etc/profile`，再运行脚本 |
| 图片未生成，只有文字 | 确认 `response_modalities` 包含 `"IMAGE"` |
| 图片质量不佳 | 换用 `gemini-3-pro-image-preview`，或优化 prompt |
| 速率限制错误 | 免费套餐有限制，稍等片刻重试 |
| 图片保存失败 | 确认 `/var/minis/attachments/` 目录存在 |

---

## 参考资源

- 官方文档：https://ai.google.dev/gemini-api/docs/image-generation
- API Key 获取：https://aistudio.google.com/apikey
