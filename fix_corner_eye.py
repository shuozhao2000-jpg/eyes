"""
精确处理右下角眼睛特写
"""
import cv2
import numpy as np

CORAL_BROWN = (130, 155, 185)

def apply_color(image, cx, cy, radius, color, intensity, feather):
    result = image.copy()
    h, w = image.shape[:2]
    
    y, x = np.ogrid[:h, :w]
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    
    mask = np.zeros((h, w), dtype=np.float32)
    inner = radius - feather
    outer = radius + feather
    
    mask[dist < inner] = 1.0
    trans = (dist >= inner) & (dist < outer)
    mask[trans] = 1.0 - (dist[trans] - inner) / (outer - inner)
    mask *= intensity
    
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    target = np.zeros((1,1,3), dtype=np.uint8)
    target[0,0] = color
    lab_t = cv2.cvtColor(target, cv2.COLOR_BGR2LAB).astype(np.float32)[0,0]
    
    lab[:,:,1] = lab[:,:,1] * (1 - mask) + lab_t[1] * mask
    lab[:,:,2] = lab[:,:,2] * (1 - mask) + lab_t[2] * mask
    
    return cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

# 加载之前处理好的图片（已经处理了模特双眼）
img = cv2.imread('output/result_coral_brown.jpg')
print(f'Loaded: {img.shape}')

# 右下角眼睛特写的精确位置
# 眼球中心约在 (656, 608)，半径约 30
EYE_CX = 656
EYE_CY = 608  
EYE_RADIUS = 32

print(f'Processing corner eye at ({EYE_CX}, {EYE_CY}), r={EYE_RADIUS}')

# 应用颜色，高强度
result = apply_color(img, EYE_CX, EYE_CY, EYE_RADIUS, CORAL_BROWN, 0.8, 8)

cv2.imwrite('output/result_final.jpg', result)
print('Saved: output/result_final.jpg')

# 细节图
detail = result[560:670, 600:720]
detail = cv2.resize(detail, (240, 220), interpolation=cv2.INTER_CUBIC)
cv2.imwrite('output/detail_corner.jpg', detail)
print('Saved: output/detail_corner.jpg')

# 对比
orig = cv2.imread('input/model.jpg')
h, w = orig.shape[:2]
comp = np.hstack([cv2.resize(orig, (w//2, h//2)), cv2.resize(result, (w//2, h//2))])
cv2.imwrite('output/comparison_final.jpg', comp)
print('Saved: output/comparison_final.jpg')

print('\n[DONE]')
