"""
美瞳叠加模块
将美瞳素材透视变换后叠加到眼球上，保留高光
"""

import cv2
import numpy as np
from typing import Tuple, Optional
import math

from iris_detector import EyeData, EyeDetectionResult


class ContactLensOverlay:
    """美瞳叠加处理器"""
    
    def __init__(self, lens_image_path: str):
        """
        初始化美瞳叠加器
        
        Args:
            lens_image_path: 美瞳PNG图片路径（需要透明通道）
        """
        # 读取带Alpha通道的图片
        self.lens_image = cv2.imread(lens_image_path, cv2.IMREAD_UNCHANGED)
        
        if self.lens_image is None:
            raise ValueError(f"无法读取美瞳图片: {lens_image_path}")
        
        # 如果没有Alpha通道，创建一个基于圆形的蒙版
        if self.lens_image.shape[2] == 3:
            print("警告: 美瞳图片没有Alpha通道，将自动创建圆形蒙版")
            self.lens_image = self._add_circular_alpha(self.lens_image)
        
        # 获取美瞳原始尺寸和中心
        self.lens_h, self.lens_w = self.lens_image.shape[:2]
        self.lens_center = (self.lens_w // 2, self.lens_h // 2)
        
        # 估算美瞳原始半径（基于Alpha通道非零区域）
        alpha = self.lens_image[:, :, 3]
        non_zero_coords = np.argwhere(alpha > 128)
        if len(non_zero_coords) > 0:
            center_y, center_x = np.mean(non_zero_coords, axis=0)
            distances = np.sqrt((non_zero_coords[:, 0] - center_y)**2 + 
                               (non_zero_coords[:, 1] - center_x)**2)
            self.lens_radius = np.percentile(distances, 95)  # 使用95百分位作为半径
            self.lens_center = (int(center_x), int(center_y))
        else:
            self.lens_radius = min(self.lens_w, self.lens_h) // 2 * 0.9
        
        print(f"美瞳素材尺寸: {self.lens_w}x{self.lens_h}")
        print(f"美瞳估算半径: {self.lens_radius:.1f}px")
        print(f"美瞳中心: {self.lens_center}")
    
    def _add_circular_alpha(self, image: np.ndarray) -> np.ndarray:
        """为没有Alpha通道的图片添加圆形蒙版"""
        h, w = image.shape[:2]
        
        # 创建圆形蒙版
        alpha = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        radius = min(w, h) // 2 - 5
        
        # 创建渐变边缘
        for r in range(radius, radius - 20, -1):
            intensity = int(255 * (r - (radius - 20)) / 20)
            cv2.circle(alpha, center, r, intensity, -1)
        cv2.circle(alpha, center, radius - 20, 255, -1)
        
        # 合并通道
        result = np.dstack([image, alpha])
        return result
    
    def apply_to_eye(
        self,
        base_image: np.ndarray,
        eye_data: EyeData,
        preserve_highlights: bool = True,
        highlight_threshold: int = 220,
        blend_mode: str = "normal",
        opacity: float = 1.0
    ) -> np.ndarray:
        """
        将美瞳应用到单只眼睛
        
        Args:
            base_image: 原始图像（BGR格式）
            eye_data: 眼睛数据
            preserve_highlights: 是否保留高光
            highlight_threshold: 高光阈值 (0-255)
            blend_mode: 混合模式 ("normal", "soft_light", "overlay")
            opacity: 不透明度 (0.0-1.0)
            
        Returns:
            处理后的图像
        """
        result = base_image.copy()
        h, w = base_image.shape[:2]
        
        # 1. 计算缩放比例
        # 美瞳应该刚好覆盖虹膜核心区域
        scale = (eye_data.radius * 2.0) / self.lens_radius  # 2.0x 覆盖完整虹膜
        
        # 2. 缩放美瞳图像
        new_w = int(self.lens_w * scale)
        new_h = int(self.lens_h * scale)
        if new_w < 10 or new_h < 10:
            print(f"警告: 缩放后尺寸过小 ({new_w}x{new_h})，跳过")
            return result
        
        scaled_lens = cv2.resize(
            self.lens_image, 
            (new_w, new_h), 
            interpolation=cv2.INTER_LINEAR
        )
        
        # 3. 应用透视变换（基于眼球朝向）
        transformed_lens = self._apply_perspective(
            scaled_lens, 
            eye_data.euler_angles,
            eye_data.radius
        )
        
        # 4. 提取原图高光（如果需要保留）
        highlight_mask = None
        if preserve_highlights:
            highlight_mask = self._extract_highlights(
                base_image, eye_data, highlight_threshold
            )
        
        # 5. Alpha混合
        result = self._alpha_blend(
            result, 
            transformed_lens, 
            eye_data.center_px, 
            highlight_mask,
            blend_mode,
            opacity
        )
        
        return result
    
    def _apply_perspective(
        self, 
        lens: np.ndarray, 
        euler_angles: Tuple[float, float, float],
        target_radius: float
    ) -> np.ndarray:
        """
        应用透视变换模拟眼球曲面
        
        Args:
            lens: 美瞳图像 (BGRA)
            euler_angles: (pitch, yaw, roll) 欧拉角
            target_radius: 目标虹膜半径
            
        Returns:
            变换后的图像
        """
        h, w = lens.shape[:2]
        pitch, yaw, roll = euler_angles
        
        # 限制角度范围防止过度变形
        max_angle = 0.4  # 约23度
        pitch = np.clip(pitch, -max_angle, max_angle)
        yaw = np.clip(yaw, -max_angle, max_angle)
        
        # 计算透视偏移量
        # yaw影响水平透视，pitch影响垂直透视
        offset_x = w * 0.15 * math.sin(yaw)
        offset_y = h * 0.15 * math.sin(pitch)
        
        # 定义源点（美瞳四角）
        src_pts = np.float32([
            [0, 0],           # 左上
            [w - 1, 0],       # 右上
            [w - 1, h - 1],   # 右下
            [0, h - 1]        # 左下
        ])
        
        # 计算目标点（根据角度变形）
        # 模拟眼球曲面的透视效果
        dst_pts = np.float32([
            [0 + offset_x, 0 + offset_y],
            [w - 1 - offset_x, 0 - offset_y],
            [w - 1 + offset_x, h - 1 + offset_y],
            [0 - offset_x, h - 1 - offset_y]
        ])
        
        # 计算透视变换矩阵
        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        # 应用变换
        transformed = cv2.warpPerspective(
            lens, 
            M, 
            (w, h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0)
        )
        
        return transformed
    
    def _extract_highlights(
        self,
        image: np.ndarray,
        eye_data: EyeData,
        threshold: int
    ) -> np.ndarray:
        """
        提取眼球区域的高光
        
        使用LAB颜色空间的L通道来检测高光区域
        """
        h, w = image.shape[:2]
        
        # 转换到LAB空间
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # 创建眼球区域蒙版（只在虹膜范围内检测高光）
        eye_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(
            eye_mask, 
            eye_data.center_px, 
            int(eye_data.radius * 1.3),  # 稍微扩大范围
            255, 
            -1
        )
        
        # 提取高光区域
        highlight_mask = np.zeros((h, w), dtype=np.uint8)
        highlight_mask[(l_channel > threshold) & (eye_mask > 0)] = 255
        
        # 轻微膨胀以平滑边缘
        kernel = np.ones((3, 3), np.uint8)
        highlight_mask = cv2.dilate(highlight_mask, kernel, iterations=1)
        
        # 高斯模糊使边缘更柔和
        highlight_mask = cv2.GaussianBlur(highlight_mask, (5, 5), 0)
        
        return highlight_mask
    
    def _alpha_blend(
        self,
        base: np.ndarray,
        overlay: np.ndarray,
        center: Tuple[int, int],
        highlight_mask: Optional[np.ndarray] = None,
        blend_mode: str = "normal",
        opacity: float = 1.0
    ) -> np.ndarray:
        """
        Alpha混合叠加，支持多种混合模式
        
        Args:
            base: 底图 (BGR)
            overlay: 叠加图 (BGRA)
            center: 叠加中心位置
            highlight_mask: 高光蒙版
            blend_mode: 混合模式
            opacity: 不透明度
            
        Returns:
            混合后的图像
        """
        result = base.copy()
        oh, ow = overlay.shape[:2]
        bh, bw = base.shape[:2]
        
        # 计算叠加区域
        x1 = center[0] - ow // 2
        y1 = center[1] - oh // 2
        x2 = x1 + ow
        y2 = y1 + oh
        
        # 计算实际可用区域（裁剪边界）
        ox1, oy1 = 0, 0
        ox2, oy2 = ow, oh
        
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
        
        # 检查区域是否有效
        if x1 >= x2 or y1 >= y2 or ox1 >= ox2 or oy1 >= oy2:
            return result
        
        # 提取重叠区域
        overlay_roi = overlay[oy1:oy2, ox1:ox2]
        base_roi = result[y1:y2, x1:x2].astype(float)
        
        # 分离通道
        overlay_bgr = overlay_roi[:, :, :3].astype(float)
        overlay_alpha = (overlay_roi[:, :, 3:4].astype(float) / 255.0) * opacity
        
        # 根据混合模式处理
        if blend_mode == "soft_light":
            # 柔光模式
            blended = self._soft_light_blend(base_roi, overlay_bgr)
        elif blend_mode == "overlay":
            # 叠加模式
            blended = self._overlay_blend(base_roi, overlay_bgr)
        else:
            # 正常模式
            blended = overlay_bgr
        
        # 应用Alpha混合
        final = overlay_alpha * blended + (1 - overlay_alpha) * base_roi
        
        # 如果有高光蒙版，将高光叠加回来
        if highlight_mask is not None:
            hl_roi = highlight_mask[y1:y2, x1:x2].astype(float)
            hl_alpha = (hl_roi / 255.0)[:, :, np.newaxis]
            # 高光区域使用原图
            final = hl_alpha * base_roi + (1 - hl_alpha) * final
        
        result[y1:y2, x1:x2] = np.clip(final, 0, 255).astype(np.uint8)
        
        return result
    
    def _soft_light_blend(self, base: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """柔光混合模式"""
        base_norm = base / 255.0
        overlay_norm = overlay / 255.0
        
        # 柔光公式
        mask = overlay_norm <= 0.5
        result = np.zeros_like(base_norm)
        result[mask] = base_norm[mask] * (2 * overlay_norm[mask] + 
                        base_norm[mask] * (1 - 2 * overlay_norm[mask]))
        result[~mask] = base_norm[~mask] * (1 - (1 - base_norm[~mask]) * 
                         (2 * overlay_norm[~mask] - 1) / base_norm[~mask])
        
        return result * 255.0
    
    def _overlay_blend(self, base: np.ndarray, overlay: np.ndarray) -> np.ndarray:
        """叠加混合模式"""
        base_norm = base / 255.0
        overlay_norm = overlay / 255.0
        
        # 叠加公式
        mask = base_norm <= 0.5
        result = np.zeros_like(base_norm)
        result[mask] = 2 * base_norm[mask] * overlay_norm[mask]
        result[~mask] = 1 - 2 * (1 - base_norm[~mask]) * (1 - overlay_norm[~mask])
        
        return result * 255.0
    
    def apply_to_both_eyes(
        self,
        image: np.ndarray,
        detection_result: EyeDetectionResult,
        preserve_highlights: bool = True,
        highlight_threshold: int = 220,
        blend_mode: str = "normal",
        opacity: float = 1.0
    ) -> np.ndarray:
        """
        将美瞳应用到双眼
        
        Args:
            image: 原始图像
            detection_result: 眼球检测结果
            preserve_highlights: 是否保留高光
            highlight_threshold: 高光阈值
            blend_mode: 混合模式
            opacity: 不透明度
            
        Returns:
            处理后的图像
        """
        result = image.copy()
        
        if detection_result.left_eye:
            result = self.apply_to_eye(
                result, 
                detection_result.left_eye, 
                preserve_highlights,
                highlight_threshold,
                blend_mode,
                opacity
            )
        
        if detection_result.right_eye:
            result = self.apply_to_eye(
                result, 
                detection_result.right_eye, 
                preserve_highlights,
                highlight_threshold,
                blend_mode,
                opacity
            )
        
        return result


def extract_lens_from_eye_image(
    eye_image_path: str,
    output_path: str,
    expand_ratio: float = 1.2
) -> str:
    """
    从眼睛照片中提取美瞳纹理（辅助工具）
    
    Args:
        eye_image_path: 带美瞳的眼睛照片
        output_path: 输出PNG路径
        expand_ratio: 提取范围扩展比例
        
    Returns:
        输出文件路径
    """
    from iris_detector import IrisDetector
    
    image = cv2.imread(eye_image_path)
    if image is None:
        raise ValueError(f"Cannot read image: {eye_image_path}")
    
    h, w = image.shape[:2]
    cx, cy = w // 2, h // 2
    radius = None
    
    # 尝试使用MediaPipe检测
    try:
        detector = IrisDetector()
        result = detector.detect(image)
        detector.close()
        
        if result.success:
            eye_data = result.left_eye or result.right_eye
            if eye_data:
                cx, cy = eye_data.center_px
                radius = int(eye_data.radius * expand_ratio)
                print(f"[OK] MediaPipe detected eye at ({cx}, {cy}), radius={radius}")
    except Exception as e:
        print(f"[WARN] MediaPipe detection failed: {e}")
    
    # 如果检测失败，使用简单模式（假设眼睛在图像中心）
    if radius is None:
        print("[INFO] Using simple center extraction mode...")
        # 对于眼睛特写图，估算虹膜占图像的比例
        # 通常虹膜半径约为图像短边的 20-35%
        radius = int(min(h, w) * 0.30)
        print(f"[INFO] Estimated center ({cx}, {cy}), radius={radius}")
    
    # 创建正方形裁剪区域
    x1 = max(0, cx - radius)
    y1 = max(0, cy - radius)
    x2 = min(w, cx + radius)
    y2 = min(h, cy + radius)
    
    # 裁剪
    cropped = image[y1:y2, x1:x2]
    
    # 创建圆形Alpha蒙版
    ch, cw = cropped.shape[:2]
    alpha = np.zeros((ch, cw), dtype=np.uint8)
    center = (cw // 2, ch // 2)
    
    # 创建渐变边缘
    edge_width = max(15, min(ch, cw) // 20)  # 动态边缘宽度
    max_radius = min(ch, cw) // 2
    for r in range(max_radius, max_radius - edge_width, -1):
        intensity = int(255 * (r - (max_radius - edge_width)) / edge_width)
        cv2.circle(alpha, center, r, intensity, -1)
    cv2.circle(alpha, center, max_radius - edge_width, 255, -1)
    
    # 合并为BGRA
    result_image = np.dstack([cropped, alpha])
    
    # 保存
    cv2.imwrite(output_path, result_image)
    print(f"[OK] Lens texture extracted to: {output_path}")
    
    return output_path


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python lens_overlay.py <模特图片> <美瞳PNG>")
        print("      python lens_overlay.py --extract <眼睛图片> <输出PNG>")
        sys.exit(1)
    
    if sys.argv[1] == "--extract":
        # 提取模式
        extract_lens_from_eye_image(sys.argv[2], sys.argv[3])
    else:
        # 叠加模式
        from iris_detector import IrisDetector
        
        model_path = sys.argv[1]
        lens_path = sys.argv[2]
        output_path = sys.argv[3] if len(sys.argv) > 3 else "output.jpg"
        
        # 检测眼睛
        image = cv2.imread(model_path)
        detector = IrisDetector()
        result = detector.detect(image)
        detector.close()
        
        if not result.success:
            print("未检测到人脸")
            sys.exit(1)
        
        # 叠加美瞳
        overlay = ContactLensOverlay(lens_path)
        output = overlay.apply_to_both_eyes(image, result)
        
        cv2.imwrite(output_path, output)
        print(f"结果已保存到: {output_path}")
        
        # 显示对比
        comparison = np.hstack([image, output])
        cv2.imshow("Before / After", comparison)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
