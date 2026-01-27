"""
手动指定位置提取美瞳素材
"""

import cv2
import numpy as np
from pathlib import Path


def extract_lens_manual(
    image_path: str,
    output_path: str,
    center_x: int,
    center_y: int,
    radius: int,
    edge_blur: int = 20
):
    """
    手动指定位置提取美瞳
    
    Args:
        image_path: 输入图片路径
        output_path: 输出PNG路径
        center_x: 眼球中心X坐标
        center_y: 眼球中心Y坐标
        radius: 提取半径
        edge_blur: 边缘羽化宽度
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    h, w = image.shape[:2]
    print(f"Image size: {w}x{h}")
    print(f"Extracting at center ({center_x}, {center_y}) with radius {radius}")
    
    # 计算裁剪区域
    x1 = max(0, center_x - radius)
    y1 = max(0, center_y - radius)
    x2 = min(w, center_x + radius)
    y2 = min(h, center_y + radius)
    
    # 裁剪
    cropped = image[y1:y2, x1:x2]
    ch, cw = cropped.shape[:2]
    
    # 创建圆形Alpha蒙版，带渐变边缘
    alpha = np.zeros((ch, cw), dtype=np.uint8)
    center = (cw // 2, ch // 2)
    max_radius = min(ch, cw) // 2
    
    # 创建渐变边缘
    for r in range(max_radius, max(0, max_radius - edge_blur), -1):
        intensity = int(255 * (max_radius - r) / edge_blur)
        intensity = min(255, intensity)
        cv2.circle(alpha, center, r, 255 - intensity, -1)
    
    # 填充中心区域
    cv2.circle(alpha, center, max(0, max_radius - edge_blur), 255, -1)
    
    # 合并为BGRA
    result = np.dstack([cropped, alpha])
    
    # 保存
    cv2.imwrite(output_path, result)
    print(f"[OK] Saved to: {output_path}")
    
    return output_path


def create_preview(
    image_path: str,
    output_path: str,
    center_x: int,
    center_y: int,
    radius: int
):
    """
    创建预览图，显示提取区域
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    preview = image.copy()
    
    # 画圆圈标记提取区域
    cv2.circle(preview, (center_x, center_y), radius, (0, 255, 0), 2)
    cv2.circle(preview, (center_x, center_y), 5, (0, 0, 255), -1)
    
    # 添加文字
    cv2.putText(preview, f"Center: ({center_x}, {center_y})", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(preview, f"Radius: {radius}", 
                (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    cv2.imwrite(output_path, preview)
    print(f"[OK] Preview saved to: {output_path}")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    
    source_eye = input_dir / "source_eye.jpg"
    
    # ============================================
    # 根据图片调整这些参数！
    # ============================================
    CENTER_X = 408    # 眼球中心X坐标
    CENTER_Y = 278    # 眼球中心Y坐标
    RADIUS = 90       # 虹膜半径（更小，只取核心虹膜纹理）
    EDGE_BLUR = 45    # 边缘羽化（更大，超柔和过渡）
    # ============================================
    
    # 创建预览
    preview_path = output_dir / "extract_preview.jpg"
    create_preview(
        str(source_eye),
        str(preview_path),
        CENTER_X,
        CENTER_Y,
        RADIUS
    )
    
    # 提取美瞳
    lens_path = output_dir / "extracted_lens.png"
    extract_lens_manual(
        str(source_eye),
        str(lens_path),
        CENTER_X,
        CENTER_Y,
        RADIUS,
        EDGE_BLUR
    )
    
    print("\n[DONE] Check the preview and adjust parameters if needed!")
