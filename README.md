# 美瞳替换工具

将美瞳素材精准贴合到模特眼睛上，保留颜色和纹理。

## 功能特点

- 📍 **MediaPipe 眼球检测** - 精确定位虹膜中心、半径和角度
- 🎨 **精准锁色叠加** - 100%保留美瞳原色，不会被AI改变
- ✨ **高光保留** - 提取原图反光并叠加在美瞳之上
- 🔄 **透视变换** - 根据眼球角度自动变形美瞳
- 🖌️ **SD Inpainting** - 低强度融合边缘，保护中心纹理

## 安装

```bash
cd D:\eyes
pip install -r requirements.txt
```

## 快速开始

### 1. 准备素材

你需要准备：
- **模特照片** - 正面清晰的人脸照片
- **美瞳PNG** - 带透明通道的美瞳素材图

### 2. 从眼睛照片提取美瞳纹理（可选）

如果你只有美瞳的试戴效果图，可以自动提取：

```bash
python main.py --extract 眼睛照片.jpg 提取的美瞳.png
```

### 3. 替换美瞳

```bash
# 基本用法
python main.py 模特.jpg 美瞳.png 输出.jpg

# 显示预览窗口
python main.py 模特.jpg 美瞳.png 输出.jpg --preview

# 调整不透明度
python main.py 模特.jpg 美瞳.png 输出.jpg --opacity 0.8

# 使用柔光混合模式
python main.py 模特.jpg 美瞳.png 输出.jpg --blend soft_light

# 禁用SD融合（更快，但边缘可能不够自然）
python main.py 模特.jpg 美瞳.png 输出.jpg --no-sd
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--opacity` | 美瞳不透明度 (0.0-1.0) | 1.0 |
| `--blend` | 混合模式: normal, soft_light, overlay | normal |
| `--no-highlight` | 不保留高光 | - |
| `--highlight-threshold` | 高光检测阈值 (0-255) | 220 |
| `--no-sd` | 禁用SD Inpainting | - |
| `--sd-url` | SD WebUI API地址 | http://127.0.0.1:7860 |
| `--denoise` | SD重绘强度 (0.0-1.0) | 0.35 |
| `--no-protect-center` | SD融合时不保护中心 | - |
| `--preview` | 显示预览窗口 | - |

## 使用SD Inpainting（可选）

如果要使用SD边缘融合功能，需要：

1. 安装 [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)
2. 启动时添加 `--api` 参数：
   ```bash
   python launch.py --api
   ```
3. 确保WebUI运行在 http://127.0.0.1:7860

不启动SD也可以使用基本功能，只是边缘融合效果会略差。

## 输出文件

运行后会生成：
- `result.jpg` - 最终结果
- `debug_landmarks.jpg` - 关键点检测可视化
- `intermediate_overlay.jpg` - SD融合前的中间结果

## 常见问题

### Q: 检测不到眼睛？
确保图片中有清晰的正面人脸，光线充足，眼睛睁开。

### Q: 美瞳位置不准？
检查美瞳PNG的中心是否对齐，可以用 `--extract` 重新提取。

### Q: 颜色不对？
本工具直接贴图，不会改变颜色。如果颜色不对，检查美瞳PNG素材本身。

### Q: 边缘不自然？
- 降低 `--denoise` 值（如0.2）
- 或提高 `--opacity` 值
- 或使用 `--blend soft_light` 混合模式

## 文件结构

```
D:\eyes\
├── main.py           # 主程序入口
├── iris_detector.py  # 眼球检测模块
├── lens_overlay.py   # 美瞳叠加模块
├── sd_refiner.py     # SD融合模块
├── requirements.txt  # 依赖列表
└── README.md         # 说明文档
```
