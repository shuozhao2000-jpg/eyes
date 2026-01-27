"""
处理右下角眼睛特写区域
"""

import cv2
import numpy as np

# 粉珊棕颜色
CORAL_BROWN = (130, 155, 185)


def apply_color_to_region(image, center, radius, target_color, intensity=0.5, feather=15):
    """对指定区域应用颜色"""
    result = image.copy()
    h, w = image.shape[:2]
    cx, cy = center
    
    y_coords, x_coords = np.ogrid[:h, :w]
    dist = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
    
    inner_radius = radius - feather
    outer_radius = radius + feather
    
    mask = np.zeros((h, w), dtype=np.float32)
    mask[dist < inner_radius] = 1.0
    transition = (dist >= inner_radius) & (dist < outer_radius)
    if np.any(transition):
        mask[transition] = 1.0 - (dist[transition] - inner_radius) / (outer_radius - inner_radius)
    mask = mask * intensity
    
    lab_original = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    target_bgr = np.zeros((1, 1, 3), dtype=np.uint8)
    target_bgr[0, 0] = target_color
    lab_target = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
    
    lab_result = lab_original.copy()
    lab_result[:, :, 1] = lab_original[:, :, 1] * (1 - mask) + lab_target[1] * mask
    lab_result[:, :, 2] = lab_original[:, :, 2] * (1 - mask) + lab_target[2] * mask
    
    result = cv2.cvtColor(np.clip(lab_result, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return result


if __name__ == "__main__":
    print('Loading current result...')
    img = cv2.imread('output/result_coral_brown.jpg')
    h, w = img.shape[:2]
    print(f'Image size: {w}x{h}')
    
    # 右下角眼睛特写区域
    # 根据图片，这个眼睛特写大概在右下角
    # 先裁剪出这个区域看看
    
    # 眼睛特写区域大概位置 (需要根据实际图片调整)
    # 从用户提供的截图来看，眼睛在一个小方框里
    
    # 右下角区域坐标 (估计)
    eye_crop_x1, eye_crop_y1 = 590, 545
    eye_crop_x2, eye_crop_y2 = 720, 665
    
    # 眼睛中心相对于裁剪区域的位置
    eye_center_x = 655  # 绝对坐标
    eye_center_y = 615  # 绝对坐标（往下调一点）
    eye_radius = 32     # 虹膜半径（稍大一点）
    
    print(f'Processing eye at ({eye_center_x}, {eye_center_y}) with radius {eye_radius}')
    
    # 应用颜色 - 强度提高到0.75
    result = apply_color_to_region(
        img,
        (eye_center_x, eye_center_y),
        eye_radius,
        CORAL_BROWN,
        intensity=0.75,  # 更强的颜色覆盖
        feather=10
    )
    
    # 保存结果
    cv2.imwrite('output/result_final.jpg', result)
    print('[OK] Saved: output/result_final.jpg')
    
    # 保存细节图
    detail = result[eye_crop_y1:eye_crop_y2, eye_crop_x1:eye_crop_x2]
    detail_large = cv2.resize(detail, (260, 240), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('output/detail_bottom_eye.jpg', detail_large)
    print('[OK] Saved: output/detail_bottom_eye.jpg')
    
    # 对比图
    comp = np.hstack([
        cv2.resize(cv2.imread('input/model.jpg'), (w//2, h//2)),
        cv2.resize(result, (w//2, h//2))
    ])
    cv2.imwrite('output/comparison_final.jpg', comp)
    print('[OK] Saved: output/comparison_final.jpg')
    
    print('\n[DONE] All eyes processed!')
