"""
眼球关键点检测模块
使用 MediaPipe FaceMesh 检测虹膜位置、半径和旋转角度
"""

import cv2
import numpy as np
import mediapipe as mp
from dataclasses import dataclass
from typing import Tuple, Optional, List
import math


@dataclass
class EyeData:
    """存储单只眼睛的数据"""
    center: np.ndarray          # 虹膜中心点 3D坐标 (x, y, z) 归一化
    center_px: Tuple[int, int]  # 虹膜中心像素坐标
    radius: float               # 虹膜像素半径
    rotation_matrix: np.ndarray # 3x3 旋转矩阵
    normal_vector: np.ndarray   # 法线向量
    iris_points_px: np.ndarray  # 虹膜边缘4个关键点的像素坐标
    euler_angles: Tuple[float, float, float]  # 欧拉角 (pitch, yaw, roll)


@dataclass  
class EyeDetectionResult:
    """双眼检测结果"""
    left_eye: Optional[EyeData]
    right_eye: Optional[EyeData]
    success: bool
    image_size: Tuple[int, int]  # (width, height)


class IrisDetector:
    """使用MediaPipe FaceMesh检测虹膜"""
    
    # 虹膜关键点索引 (refine_landmarks=True 时可用)
    # 参考: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
    LEFT_IRIS_CENTER = 468
    RIGHT_IRIS_CENTER = 473
    LEFT_IRIS_POINTS = [469, 470, 471, 472]   # 左眼虹膜边缘4点 (上、外、下、内)
    RIGHT_IRIS_POINTS = [474, 475, 476, 477]  # 右眼虹膜边缘4点
    
    # 眼睛轮廓关键点 (用于辅助计算)
    LEFT_EYE_CONTOUR = [33, 133, 160, 159, 158, 144, 145, 153]
    RIGHT_EYE_CONTOUR = [362, 263, 387, 386, 385, 373, 374, 380]
    
    def __init__(self, static_image_mode: bool = True):
        """
        初始化检测器
        
        Args:
            static_image_mode: True用于处理静态图片，False用于视频流
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=1,
            refine_landmarks=True,  # 启用虹膜关键点 (478个点)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detect(self, image: np.ndarray) -> EyeDetectionResult:
        """
        检测图像中的眼球关键点
        
        Args:
            image: BGR格式的OpenCV图像
            
        Returns:
            EyeDetectionResult: 包含双眼数据的结果
        """
        h, w = image.shape[:2]
        
        # 转换为RGB (MediaPipe要求)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_image)
        
        if not results.multi_face_landmarks:
            return EyeDetectionResult(None, None, False, (w, h))
        
        landmarks = results.multi_face_landmarks[0].landmark
        
        # 提取左眼数据
        left_eye = self._extract_eye_data(
            landmarks, w, h,
            self.LEFT_IRIS_CENTER,
            self.LEFT_IRIS_POINTS,
            is_left=True
        )
        
        # 提取右眼数据
        right_eye = self._extract_eye_data(
            landmarks, w, h,
            self.RIGHT_IRIS_CENTER,
            self.RIGHT_IRIS_POINTS,
            is_left=False
        )
        
        return EyeDetectionResult(left_eye, right_eye, True, (w, h))
    
    def _extract_eye_data(
        self, 
        landmarks, 
        w: int, 
        h: int,
        center_idx: int,
        iris_indices: List[int],
        is_left: bool
    ) -> EyeData:
        """提取单只眼睛的完整数据"""
        
        # 1. 提取中心点3D坐标
        center_lm = landmarks[center_idx]
        center_3d = np.array([center_lm.x, center_lm.y, center_lm.z])
        center_px = (int(center_lm.x * w), int(center_lm.y * h))
        
        # 2. 提取虹膜边缘4个点
        iris_points_3d = []
        iris_points_px = []
        for idx in iris_indices:
            lm = landmarks[idx]
            iris_points_3d.append([lm.x, lm.y, lm.z])
            iris_points_px.append([lm.x * w, lm.y * h])
        iris_points_3d = np.array(iris_points_3d)
        iris_points_px = np.array(iris_points_px)
        
        # 3. 计算虹膜半径（取4个边缘点到中心的平均距离）
        center_2d = np.array([center_lm.x * w, center_lm.y * h])
        distances = np.linalg.norm(iris_points_px - center_2d, axis=1)
        radius = np.mean(distances)
        
        # 4. 计算法线向量和旋转矩阵
        normal_vector, rotation_matrix, euler_angles = self._compute_orientation(
            center_3d, iris_points_3d, is_left
        )
        
        return EyeData(
            center=center_3d,
            center_px=center_px,
            radius=radius,
            rotation_matrix=rotation_matrix,
            normal_vector=normal_vector,
            iris_points_px=iris_points_px,
            euler_angles=euler_angles
        )
    
    def _compute_orientation(
        self, 
        center: np.ndarray, 
        iris_points: np.ndarray,
        is_left: bool
    ) -> Tuple[np.ndarray, np.ndarray, Tuple[float, float, float]]:
        """
        计算虹膜的法线向量、旋转矩阵和欧拉角
        
        基于虹膜边缘4点拟合平面来估算眼球朝向
        """
        # 将点相对于中心归一化
        relative_points = iris_points - center
        
        # 使用SVD拟合平面，获取法线向量
        # 法线是最小奇异值对应的右奇异向量
        try:
            _, _, vh = np.linalg.svd(relative_points)
            normal = vh[-1]  # 法线向量
        except:
            # SVD失败时使用默认法线
            normal = np.array([0, 0, -1])
        
        # 确保法线指向相机（z分量为负）
        if normal[2] > 0:
            normal = -normal
        
        # 归一化
        normal = normal / (np.linalg.norm(normal) + 1e-8)
        
        # 计算欧拉角 (从法线向量)
        # pitch: 绕X轴旋转 (上下看)
        # yaw: 绕Y轴旋转 (左右看)
        pitch = math.asin(np.clip(-normal[1], -1, 1))
        yaw = math.atan2(normal[0], -normal[2])
        roll = 0  # 简化处理，假设无滚转
        
        euler_angles = (pitch, yaw, roll)
        
        # 构建旋转矩阵（从正面视角到当前视角）
        rotation_matrix = self._euler_to_rotation_matrix(pitch, yaw, roll)
        
        return normal, rotation_matrix, euler_angles
    
    def _euler_to_rotation_matrix(
        self, 
        pitch: float, 
        yaw: float, 
        roll: float
    ) -> np.ndarray:
        """将欧拉角转换为旋转矩阵"""
        # Rotation around X-axis (pitch)
        Rx = np.array([
            [1, 0, 0],
            [0, math.cos(pitch), -math.sin(pitch)],
            [0, math.sin(pitch), math.cos(pitch)]
        ])
        
        # Rotation around Y-axis (yaw)
        Ry = np.array([
            [math.cos(yaw), 0, math.sin(yaw)],
            [0, 1, 0],
            [-math.sin(yaw), 0, math.cos(yaw)]
        ])
        
        # Rotation around Z-axis (roll)
        Rz = np.array([
            [math.cos(roll), -math.sin(roll), 0],
            [math.sin(roll), math.cos(roll), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation matrix
        R = Rz @ Ry @ Rx
        return R
    
    def draw_landmarks(
        self, 
        image: np.ndarray, 
        result: EyeDetectionResult,
        draw_iris: bool = True,
        draw_center: bool = True,
        draw_radius: bool = True
    ) -> np.ndarray:
        """
        在图像上绘制检测结果（用于调试）
        
        Args:
            image: 原始图像
            result: 检测结果
            draw_iris: 是否绘制虹膜边缘点
            draw_center: 是否绘制中心点
            draw_radius: 是否绘制半径圆
            
        Returns:
            绘制后的图像
        """
        output = image.copy()
        
        for eye_data, color in [(result.left_eye, (0, 255, 0)), 
                                 (result.right_eye, (0, 0, 255))]:
            if eye_data is None:
                continue
            
            # 绘制中心点
            if draw_center:
                cv2.circle(output, eye_data.center_px, 3, color, -1)
            
            # 绘制半径圆
            if draw_radius:
                cv2.circle(output, eye_data.center_px, int(eye_data.radius), color, 1)
            
            # 绘制虹膜边缘点
            if draw_iris:
                for pt in eye_data.iris_points_px:
                    cv2.circle(output, (int(pt[0]), int(pt[1])), 2, (255, 255, 0), -1)
        
        return output
    
    def close(self):
        """释放资源"""
        self.face_mesh.close()


def detect_eyes(image_path: str) -> EyeDetectionResult:
    """
    便捷函数：从图像路径获取眼球数据
    
    Args:
        image_path: 图像文件路径
        
    Returns:
        EyeDetectionResult: 双眼检测结果
    """
    detector = IrisDetector()
    image = cv2.imread(image_path)
    
    if image is None:
        raise ValueError(f"无法读取图像: {image_path}")
    
    result = detector.detect(image)
    detector.close()
    
    return result


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python iris_detector.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"无法读取图像: {image_path}")
        sys.exit(1)
    
    detector = IrisDetector()
    result = detector.detect(image)
    
    if result.success:
        print("检测成功!")
        
        if result.left_eye:
            print(f"\n左眼:")
            print(f"  中心像素: {result.left_eye.center_px}")
            print(f"  半径: {result.left_eye.radius:.1f}px")
            print(f"  欧拉角 (pitch, yaw, roll): {tuple(f'{a:.2f}' for a in result.left_eye.euler_angles)}")
        
        if result.right_eye:
            print(f"\n右眼:")
            print(f"  中心像素: {result.right_eye.center_px}")
            print(f"  半径: {result.right_eye.radius:.1f}px")
            print(f"  欧拉角 (pitch, yaw, roll): {tuple(f'{a:.2f}' for a in result.right_eye.euler_angles)}")
        
        # 绘制并显示结果
        output = detector.draw_landmarks(image, result)
        cv2.imshow("Eye Detection", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("未检测到人脸")
    
    detector.close()
