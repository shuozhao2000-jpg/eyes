"""
手动定位提取美瞳纹理，然后贴到右下角眼睛
"""
import cv2
import numpy as np

# ============================================
# 第一步：从source_eye.jpg提取完整美瞳（使用手动定位的四边配置）
# ============================================
SOURCE_CX = 451       # 圆心X
SOURCE_CY = 242       # 圆心Y
SOURCE_TOP = 96       # 上边距离
SOURCE_BOTTOM = 131   # 下边距离
SOURCE_LEFT = 130     # 左边距离
SOURCE_RIGHT = 127    # 右边距离
SOURCE_FEATHER = 30   # 边缘羽化
# ============================================

# ============================================
# 第二步：贴到右下角眼睛的参数（使用交互式定位的参数）
# ============================================
TARGET_CX = 644     # 右下角眼球中心X
TARGET_CY = 654     # 右下角眼球中心Y
TARGET_RADIUS = 34  # 目标虹膜半径（手动定位）
SCALE_FACTOR = 1.1  # 缩放倍数（稍微放大以覆盖清除区域）
# ============================================


def extract_full_lens(image_path, cx, cy, top, bottom, left, right, feather):
    """从图片中提取四边可调的不规则形状美瞳"""
    img = cv2.imread(image_path)
    h, w = img.shape[:2]
    
    # 裁剪区域（使用最大距离）
    max_r = max(top, bottom, left, right)
    x1 = max(0, cx - max_r)
    y1 = max(0, cy - max_r)
    x2 = min(w, cx + max_r)
    y2 = min(h, cy + max_r)
    
    cropped = img[y1:y2, x1:x2].copy()
    ch, cw = cropped.shape[:2]
    center_x = cx - x1
    center_y = cy - y1
    
    # 创建四边可调的Alpha蒙版
    alpha = np.zeros((ch, cw), dtype=np.float32)
    
    for y in range(ch):
        for x in range(cw):
            dx = x - center_x
            dy = y - center_y
            
            # 根据位置选择对应的边距离
            if dy < 0:  # 上半部分
                ry = top
            else:  # 下半部分
                ry = bottom
                
            if dx < 0:  # 左半部分
                rx = left
            else:  # 右半部分
                rx = right
            
            # 计算椭圆距离（归一化）
            if rx > 0 and ry > 0:
                ellipse_dist = np.sqrt((dx / rx)**2 + (dy / ry)**2)
            else:
                ellipse_dist = 999
            
            if ellipse_dist > 1:
                alpha[y, x] = 0
            elif ellipse_dist > 1 - feather / max(rx, ry):
                # 边缘羽化
                alpha[y, x] = (1 - ellipse_dist) / (feather / max(rx, ry))
            else:
                alpha[y, x] = 1.0
    
    alpha = (alpha * 255).astype(np.uint8)
    
    # 合并BGRA
    result = np.dstack([cropped, alpha])
    return result


def clear_iris_to_white(image, cx, cy, radius, feather=5):
    """将指定区域清除为纯白色（使用手动定位的参数）"""
    result = image.copy()
    h, w = image.shape[:2]
    
    # 使用纯白色
    pure_white = np.array([255, 255, 255], dtype=np.uint8)
    
    # 稍微缩小清除范围，避免白边
    clear_radius = int(radius * 0.85)
    
    # 创建渐变遮罩
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    
    mask = np.zeros((h, w), dtype=np.float32)
    inner = clear_radius - feather
    outer = clear_radius
    
    # 完全覆盖内部区域
    mask[dist < inner] = 1.0
    transition = (dist >= inner) & (dist < outer)
    if np.any(transition):
        mask[transition] = 1.0 - (dist[transition] - inner) / (outer - inner)
    
    # 应用纯白色
    for c in range(3):
        result[:, :, c] = (result[:, :, c] * (1 - mask) + pure_white[c] * mask).astype(np.uint8)
    
    return result


def apply_texture_to_eye(base_image, texture, target_cx, target_cy, target_radius, 
                          scale_factor=1.0, clear_first=False, preserve_highlights=True, highlight_threshold=210):
    """将纹理贴到目标眼睛上"""
    result = base_image.copy()
    
    # 先清除原有虹膜（变成眼白）
    if clear_first:
        result = clear_iris_to_white(result, target_cx, target_cy, target_radius, feather=3)
    
    # 计算缩放比例：让纹理外圈正好匹配目标虹膜半径
    th, tw = texture.shape[:2]
    texture_radius = min(th, tw) // 2
    # 精确匹配：纹理半径 -> 目标半径
    scale = (target_radius / texture_radius) * scale_factor
    
    # 缩放纹理
    new_w = int(tw * scale)
    new_h = int(th * scale)
    scaled = cv2.resize(texture, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # 计算叠加位置
    x1 = target_cx - new_w // 2
    y1 = target_cy - new_h // 2
    x2 = x1 + new_w
    y2 = y1 + new_h
    
    # 边界检查
    bh, bw = base_image.shape[:2]
    ox1, oy1 = 0, 0
    ox2, oy2 = new_w, new_h
    
    if x1 < 0:
        ox1 = -x1
        x1 = 0
    if y1 < 0:
        oy1 = -y1
        y1 = 0
    if x2 > bw:
        ox2 -= (x2 - bw)
        x2 = bw
    if y2 > bh:
        oy2 -= (y2 - bh)
        y2 = bh
    
    if x1 >= x2 or y1 >= y2:
        return result
    
    # 提取ROI
    overlay_roi = scaled[oy1:oy2, ox1:ox2]
    base_roi = result[y1:y2, x1:x2].astype(float)
    
    # 分离通道
    overlay_bgr = overlay_roi[:, :, :3].astype(float)
    overlay_alpha = overlay_roi[:, :, 3:4].astype(float) / 255.0
    
    # 提取目标眼睛的高光
    if preserve_highlights:
        lab = cv2.cvtColor(base_image[y1:y2, x1:x2], cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        target_highlight_mask = (l_channel > highlight_threshold).astype(float)
        target_highlight_mask = cv2.GaussianBlur(target_highlight_mask, (5, 5), 0)[:, :, np.newaxis]
    else:
        target_highlight_mask = None
    
    # 检测并排除源纹理中的高光区域（只排除非常亮的窗户反光边框）
    overlay_gray = cv2.cvtColor(overlay_roi[:, :, :3], cv2.COLOR_BGR2GRAY)
    source_highlight = (overlay_gray > 220).astype(float)  # 只排除非常亮的部分
    source_highlight = cv2.GaussianBlur(source_highlight, (5, 5), 0)[:, :, np.newaxis]
    # 在源纹理高光处部分降低透明度
    overlay_alpha = overlay_alpha * (1 - source_highlight * 0.7)
    
    # Alpha混合
    blended = overlay_alpha * overlay_bgr + (1 - overlay_alpha) * base_roi
    
    # 保留目标眼睛的高光
    if target_highlight_mask is not None:
        blended = target_highlight_mask * base_roi + (1 - target_highlight_mask) * blended
    
    result[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
    
    return result


def create_source_preview(image_path, cx, cy, top, bottom, left, right):
    """创建源图片预览（显示四边可调的提取区域）"""
    img = cv2.imread(image_path)
    preview = img.copy()
    
    # 画四边可调的形状
    points = []
    for i in range(72):
        angle = 2 * np.pi * i / 72
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        ry = top if sin_a < 0 else bottom
        rx = left if cos_a < 0 else right
        px = int(cx + rx * cos_a)
        py = int(cy + ry * sin_a)
        points.append([px, py])
    points = np.array(points, dtype=np.int32)
    cv2.polylines(preview, [points], True, (0, 255, 0), 2)
    
    cv2.circle(preview, (cx, cy), 3, (0, 0, 255), -1)
    cv2.putText(preview, f"Center: ({cx}, {cy})", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(preview, f"T:{top} B:{bottom} L:{left} R:{right}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return preview


def create_target_preview(image_path, cx, cy, radius):
    """创建目标位置预览"""
    img = cv2.imread(image_path)
    preview = img.copy()
    cv2.circle(preview, (cx, cy), radius, (0, 255, 0), 2)
    cv2.circle(preview, (cx, cy), 3, (0, 0, 255), -1)
    
    # 裁剪右下角区域
    crop = preview[550:700, 580:760]
    crop = cv2.resize(crop, (360, 300), interpolation=cv2.INTER_CUBIC)
    cv2.putText(crop, f"Target: ({cx}, {cy}), r={radius}", (10, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return crop


if __name__ == "__main__":
    print("=" * 50)
    print("  手动纹理替换工具")
    print("=" * 50)
    
    # 1. 预览源图片定位
    print("\n[1] 创建源图片预览...")
    source_preview = create_source_preview('input/source_eye.jpg', 
                                            SOURCE_CX, SOURCE_CY, 
                                            SOURCE_TOP, SOURCE_BOTTOM, SOURCE_LEFT, SOURCE_RIGHT)
    cv2.imwrite('output/source_preview.jpg', source_preview)
    print("    Saved: output/source_preview.jpg")
    
    # 2. 预览目标位置
    print("\n[2] 创建目标位置预览...")
    target_preview = create_target_preview('output/result_coral_brown.jpg',
                                            TARGET_CX, TARGET_CY, TARGET_RADIUS)
    cv2.imwrite('output/target_preview.jpg', target_preview)
    print("    Saved: output/target_preview.jpg")
    
    # 3. 提取四边可调的美瞳
    print("\n[3] 提取美瞳纹理...")
    texture = extract_full_lens('input/source_eye.jpg',
                                 SOURCE_CX, SOURCE_CY, 
                                 SOURCE_TOP, SOURCE_BOTTOM, SOURCE_LEFT, SOURCE_RIGHT,
                                 SOURCE_FEATHER)
    cv2.imwrite('output/extracted_texture.png', texture)
    print("    Saved: output/extracted_texture.png")
    
    # 4. 直接贴新纹理（不清除为白色）
    print("\n[4] 直接贴新美瞳纹理...")
    print(f"    目标位置: ({TARGET_CX}, {TARGET_CY}), 半径: {TARGET_RADIUS}")
    print(f"    缩放倍数: {SCALE_FACTOR}")
    base_img = cv2.imread('output/result_coral_brown.jpg')
    
    # 直接贴纹理，不先清除为白色
    result = apply_texture_to_eye(base_img, texture, 
                                   TARGET_CX, TARGET_CY, TARGET_RADIUS,
                                   scale_factor=SCALE_FACTOR,
                                   clear_first=False,
                                   preserve_highlights=True)
    cv2.imwrite('output/result_texture.jpg', result)
    print("    Saved: output/result_texture.jpg")
    
    # 5. 细节图
    detail = result[550:700, 580:760]
    detail = cv2.resize(detail, (360, 300), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('output/texture_detail.jpg', detail)
    print("    Saved: output/texture_detail.jpg")
    
    print("\n" + "=" * 50)
    print("  完成！请检查预览图确认定位是否正确")
    print("=" * 50)
