"""
手动定位右下角眼睛 - 带预览功能
"""
import cv2
import numpy as np

# ============================================
# 调整这些参数来定位右下角眼睛！
# ============================================
EYE_CX = 644      # 眼球中心X坐标（再往左一点）
EYE_CY = 654      # 眼球中心Y坐标（再往下一点）
EYE_RADIUS = 26   # 虹膜半径
# ============================================

CORAL_BROWN = (130, 155, 185)


def create_preview(img, cx, cy, radius):
    """创建预览图，显示定位圆圈"""
    preview = img.copy()
    
    # 画定位圆圈
    cv2.circle(preview, (cx, cy), radius, (0, 255, 0), 2)
    cv2.circle(preview, (cx, cy), 3, (0, 0, 255), -1)
    
    # 裁剪右下角区域并放大显示
    crop = preview[550:680, 580:750]
    crop_large = cv2.resize(crop, (340, 260), interpolation=cv2.INTER_CUBIC)
    
    # 添加坐标文字
    cv2.putText(crop_large, f"Center: ({cx}, {cy})", (10, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(crop_large, f"Radius: {radius}", (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    return crop_large


def apply_color(image, cx, cy, radius, color, intensity=0.8, feather=8):
    """应用颜色到指定位置"""
    result = image.copy()
    h, w = image.shape[:2]
    
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    
    mask = np.zeros((h, w), dtype=np.float32)
    inner = radius - feather
    outer = radius + feather
    
    mask[dist < inner] = 1.0
    trans = (dist >= inner) & (dist < outer)
    if np.any(trans):
        mask[trans] = 1.0 - (dist[trans] - inner) / (outer - inner)
    mask *= intensity
    
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    target = np.zeros((1,1,3), dtype=np.uint8)
    target[0,0] = color
    lab_t = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
    
    lab[:,:,1] = lab[:,:,1] * (1 - mask) + lab_t[1] * mask
    lab[:,:,2] = lab[:,:,2] * (1 - mask) + lab_t[2] * mask
    
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)


if __name__ == "__main__":
    # 读取已处理好模特双眼的图片
    img = cv2.imread('output/result_coral_brown.jpg')
    print(f'Image loaded: {img.shape}')
    
    # 1. 先创建预览图，确认定位
    print(f'\nCurrent settings:')
    print(f'  Center: ({EYE_CX}, {EYE_CY})')
    print(f'  Radius: {EYE_RADIUS}')
    
    preview = create_preview(img, EYE_CX, EYE_CY, EYE_RADIUS)
    cv2.imwrite('output/corner_preview.jpg', preview)
    print('\n[PREVIEW] Saved: output/corner_preview.jpg')
    print('Check the preview to see if the circle is correctly positioned!')
    
    # 2. 应用颜色
    result = apply_color(img, EYE_CX, EYE_CY, EYE_RADIUS, CORAL_BROWN, 0.8, 8)
    cv2.imwrite('output/result_final.jpg', result)
    print('[RESULT] Saved: output/result_final.jpg')
    
    # 3. 细节图
    detail = result[550:680, 580:750]
    detail = cv2.resize(detail, (340, 260), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('output/corner_detail.jpg', detail)
    print('[DETAIL] Saved: output/corner_detail.jpg')
