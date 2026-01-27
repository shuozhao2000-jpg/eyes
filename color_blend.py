"""
颜色混合方法 - 只改变虹膜颜色，不添加纹理边缘
这种方法可以避免产生边缘印记
"""

import cv2
import numpy as np
from pathlib import Path
from iris_detector import IrisDetector


def get_dominant_color(image_path: str) -> tuple:
    """从美瞳素材中提取主色调"""
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    
    if img.shape[2] == 4:
        # 只考虑不透明的像素
        alpha = img[:, :, 3]
        mask = alpha > 128
        pixels = img[:, :, :3][mask]
    else:
        pixels = img.reshape(-1, 3)
    
    # 计算平均颜色
    avg_color = np.mean(pixels, axis=0).astype(int)
    
    # 也计算主要颜色（使用K-means）
    from sklearn.cluster import KMeans
    try:
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(pixels)
        # 取最大的簇作为主色
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        dominant_idx = labels[np.argmax(counts)]
        dominant_color = kmeans.cluster_centers_[dominant_idx].astype(int)
        return tuple(dominant_color), tuple(avg_color)
    except:
        return tuple(avg_color), tuple(avg_color)


def apply_color_to_iris(
    model_image: np.ndarray,
    eye_center: tuple,
    eye_radius: float,
    target_color: tuple,  # BGR
    intensity: float = 0.4,
    feather: int = 15
) -> np.ndarray:
    """
    将目标颜色应用到虹膜区域
    使用颜色混合模式，只改变色调不添加纹理
    """
    result = model_image.copy()
    h, w = model_image.shape[:2]
    
    # 创建虹膜区域蒙版
    mask = np.zeros((h, w), dtype=np.float32)
    
    # 绘制渐变圆形蒙版
    cx, cy = eye_center
    for y in range(max(0, cy - int(eye_radius) - feather), 
                   min(h, cy + int(eye_radius) + feather)):
        for x in range(max(0, cx - int(eye_radius) - feather), 
                       min(w, cx + int(eye_radius) + feather)):
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            if dist < eye_radius - feather:
                mask[y, x] = 1.0
            elif dist < eye_radius + feather:
                # 渐变过渡
                mask[y, x] = 1.0 - (dist - (eye_radius - feather)) / (2 * feather)
    
    # 创建颜色叠加层
    color_layer = np.zeros_like(model_image, dtype=np.float32)
    color_layer[:, :] = target_color
    
    # 转换到LAB空间进行颜色混合
    lab_original = cv2.cvtColor(model_image, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab_color = cv2.cvtColor(color_layer.astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    
    # 只混合a和b通道（色度），保留原始L通道（亮度）
    lab_result = lab_original.copy()
    
    for i in range(h):
        for j in range(w):
            if mask[i, j] > 0:
                blend = mask[i, j] * intensity
                # 保留原始亮度，混合色度
                lab_result[i, j, 1] = lab_original[i, j, 1] * (1 - blend) + lab_color[i, j, 1] * blend
                lab_result[i, j, 2] = lab_original[i, j, 2] * (1 - blend) + lab_color[i, j, 2] * blend
    
    # 转回BGR
    result = cv2.cvtColor(lab_result.astype(np.uint8), cv2.COLOR_LAB2BGR)
    
    return result


def apply_color_fast(
    model_image: np.ndarray,
    eye_center: tuple,
    eye_radius: float,
    target_color: tuple,  # BGR
    intensity: float = 0.5,
    feather: int = 20
) -> np.ndarray:
    """
    快速颜色混合（使用numpy向量化）
    """
    result = model_image.copy().astype(np.float32)
    h, w = model_image.shape[:2]
    
    cx, cy = eye_center
    
    # 创建坐标网格
    y_coords, x_coords = np.ogrid[:h, :w]
    
    # 计算到中心的距离
    dist = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
    
    # 创建渐变蒙版
    inner_radius = eye_radius - feather
    outer_radius = eye_radius + feather
    
    mask = np.zeros((h, w), dtype=np.float32)
    mask[dist < inner_radius] = 1.0
    
    transition = (dist >= inner_radius) & (dist < outer_radius)
    mask[transition] = 1.0 - (dist[transition] - inner_radius) / (outer_radius - inner_radius)
    
    # 应用强度
    mask = mask * intensity
    
    # 转换到HSV进行颜色混合
    hsv_original = cv2.cvtColor(model_image, cv2.COLOR_BGR2HSV).astype(np.float32)
    
    # 目标颜色的HSV
    target_bgr = np.uint8([[target_color]])
    target_hsv = cv2.cvtColor(target_bgr, cv2.COLOR_BGR2HSV)[0, 0].astype(np.float32)
    
    # 混合H和S通道，保留V（亮度）
    hsv_result = hsv_original.copy()
    
    mask_3d = mask[:, :, np.newaxis]
    
    # 只修改色相和饱和度
    hsv_result[:, :, 0] = hsv_original[:, :, 0] * (1 - mask) + target_hsv[0] * mask
    hsv_result[:, :, 1] = hsv_original[:, :, 1] * (1 - mask) + target_hsv[1] * mask
    
    # 确保值在有效范围内
    hsv_result[:, :, 0] = np.clip(hsv_result[:, :, 0], 0, 179)
    hsv_result[:, :, 1] = np.clip(hsv_result[:, :, 1], 0, 255)
    
    result = cv2.cvtColor(hsv_result.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    return result


def process_with_color_blend(
    model_path: str,
    lens_path: str,
    output_path: str,
    intensity: float = 0.45,
    feather: int = 18
):
    """完整的颜色混合处理流程"""
    
    print("Loading images...")
    model_img = cv2.imread(model_path)
    
    print("Detecting eyes...")
    detector = IrisDetector()
    result = detector.detect(model_img)
    detector.close()
    
    if not result.success:
        raise ValueError("No face detected")
    
    # 从美瞳素材提取目标颜色
    print("Extracting target color from lens...")
    try:
        dominant_color, avg_color = get_dominant_color(lens_path)
        print(f"  Dominant color (BGR): {dominant_color}")
        print(f"  Average color (BGR): {avg_color}")
        target_color = dominant_color
    except Exception as e:
        print(f"  Using fallback color extraction: {e}")
        lens_img = cv2.imread(lens_path)
        target_color = tuple(np.mean(lens_img.reshape(-1, 3), axis=0).astype(int))
    
    output = model_img.copy()
    
    # 处理左眼
    if result.left_eye:
        print(f"Processing left eye at {result.left_eye.center_px}...")
        output = apply_color_fast(
            output,
            result.left_eye.center_px,
            result.left_eye.radius * 1.1,  # 稍微扩大一点
            target_color,
            intensity,
            feather
        )
    
    # 处理右眼
    if result.right_eye:
        print(f"Processing right eye at {result.right_eye.center_px}...")
        output = apply_color_fast(
            output,
            result.right_eye.center_px,
            result.right_eye.radius * 1.1,
            target_color,
            intensity,
            feather
        )
    
    cv2.imwrite(output_path, output)
    print(f"[DONE] Saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    
    model_path = base_dir / "input" / "model.jpg"
    lens_path = base_dir / "output" / "extracted_lens.png"
    
    # 多个强度版本
    for intensity in [0.35, 0.45, 0.55]:
        output_path = base_dir / "output" / f"result_color_blend_{int(intensity*100)}.jpg"
        process_with_color_blend(
            str(model_path),
            str(lens_path),
            str(output_path),
            intensity=intensity,
            feather=20
        )
    
    # 创建对比图
    model_img = cv2.imread(str(model_path))
    result_img = cv2.imread(str(base_dir / "output" / "result_color_blend_45.jpg"))
    h, w = model_img.shape[:2]
    comp = np.hstack([
        cv2.resize(model_img, (w//2, h//2)),
        cv2.resize(result_img, (w//2, h//2))
    ])
    cv2.imwrite(str(base_dir / "output" / "comparison_color_blend.jpg"), comp)
    print("\n[DONE] All color blend versions saved!")
