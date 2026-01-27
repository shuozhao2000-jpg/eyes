"""
修正颜色 - 使用正确的粉珊棕色
"""

import cv2
import numpy as np
from iris_detector import IrisDetector

# 粉珊棕的正确颜色 (BGR格式)
# 暖棕色带粉调
CORAL_BROWN = (130, 155, 185)


def apply_color(model_image, eye_center, eye_radius, target_color, intensity=0.5, feather=18):
    """使用LAB颜色空间进行颜色混合"""
    result = model_image.copy()
    h, w = model_image.shape[:2]
    cx, cy = eye_center
    
    # 创建蒙版
    y_coords, x_coords = np.ogrid[:h, :w]
    dist = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
    
    inner_radius = eye_radius - feather
    outer_radius = eye_radius + feather
    
    mask = np.zeros((h, w), dtype=np.float32)
    mask[dist < inner_radius] = 1.0
    transition = (dist >= inner_radius) & (dist < outer_radius)
    mask[transition] = 1.0 - (dist[transition] - inner_radius) / (outer_radius - inner_radius)
    mask = mask * intensity
    
    # LAB颜色空间混合
    lab_original = cv2.cvtColor(model_image, cv2.COLOR_BGR2LAB).astype(np.float32)
    
    target_bgr = np.zeros((1, 1, 3), dtype=np.uint8)
    target_bgr[0, 0] = target_color
    lab_target = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)[0, 0]
    
    lab_result = lab_original.copy()
    # 只混合a和b通道（色度），保留L（亮度）
    lab_result[:, :, 1] = lab_original[:, :, 1] * (1 - mask) + lab_target[1] * mask
    lab_result[:, :, 2] = lab_original[:, :, 2] * (1 - mask) + lab_target[2] * mask
    
    result = cv2.cvtColor(np.clip(lab_result, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return result


if __name__ == "__main__":
    print('Loading...')
    model_img = cv2.imread('input/model.jpg')
    
    detector = IrisDetector()
    result = detector.detect(model_img)
    detector.close()
    
    print(f'Left eye: {result.left_eye.center_px}')
    print(f'Right eye: {result.right_eye.center_px}')
    
    # 应用粉珊棕颜色
    output = model_img.copy()
    
    if result.left_eye:
        output = apply_color(
            output, 
            result.left_eye.center_px, 
            result.left_eye.radius * 1.1,
            CORAL_BROWN,
            intensity=0.5,
            feather=18
        )
    
    if result.right_eye:
        output = apply_color(
            output, 
            result.right_eye.center_px, 
            result.right_eye.radius * 1.1,
            CORAL_BROWN,
            intensity=0.5,
            feather=18
        )
    
    cv2.imwrite('output/result_coral_brown.jpg', output)
    
    # 生成眼睛细节图
    eye_region = output[200:350, 420:680]
    eye_detail = cv2.resize(eye_region, (520, 300), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite('output/detail_coral_brown.jpg', eye_detail)
    
    # 对比图
    h, w = model_img.shape[:2]
    comp = np.hstack([
        cv2.resize(model_img, (w//2, h//2)), 
        cv2.resize(output, (w//2, h//2))
    ])
    cv2.imwrite('output/comparison_coral_brown.jpg', comp)
    
    print('[DONE] Coral brown version saved!')
