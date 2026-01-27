"""
Stable Diffusion Inpainting 边缘融合模块
使用低强度重绘处理美瞳边缘，使其自然融入眼睛
"""

import cv2
import numpy as np
import requests
import base64
from typing import Optional, Tuple
from io import BytesIO

from iris_detector import EyeDetectionResult


class SDInpaintingRefiner:
    """使用Stable Diffusion Inpainting进行边缘融合"""
    
    def __init__(
        self, 
        api_url: str = "http://127.0.0.1:7860",
        timeout: int = 120
    ):
        """
        初始化SD Inpainting
        
        Args:
            api_url: Stable Diffusion WebUI API地址
            timeout: API请求超时时间（秒）
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        
        # 默认提示词 - 专门针对眼睛融合优化
        self.default_prompt = (
            "extremely realistic eyes, wet texture, sharp focus, "
            "8k resolution, seamless iris integration, natural eye reflection, "
            "detailed eyelashes, realistic skin texture around eyes"
        )
        
        self.default_negative_prompt = (
            "blurry, low quality, artificial, fake looking, "
            "wrong iris color, changed iris pattern, distorted pupil, "
            "asymmetric eyes, unnatural highlights, plastic skin"
        )
    
    def check_api_available(self) -> bool:
        """检查SD WebUI API是否可用"""
        try:
            response = requests.get(
                f"{self.api_url}/sdapi/v1/sd-models",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def generate_edge_mask(
        self,
        image: np.ndarray,
        detection_result: EyeDetectionResult,
        expand_pixels: int = 5,
        edge_width: int = 15,
        protect_center_ratio: float = 0.65
    ) -> np.ndarray:
        """
        生成环形Inpainting蒙版 - 只处理边缘，保护中心纹理
        
        Args:
            image: 原始图像
            detection_result: 眼球检测结果
            expand_pixels: 外边缘扩展像素
            edge_width: 边缘环带宽度
            protect_center_ratio: 保护中心区域比例 (0-1)
            
        Returns:
            蒙版图像（白色为重绘区域）
        """
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        for eye_data in [detection_result.left_eye, detection_result.right_eye]:
            if eye_data is None:
                continue
            
            center = eye_data.center_px
            radius = eye_data.radius
            
            # 外圈半径
            outer_radius = int(radius + expand_pixels)
            
            # 内圈半径（保护区域）
            inner_radius = int(radius * protect_center_ratio)
            
            # 绘制外圈（白色）
            cv2.circle(mask, center, outer_radius, 255, -1)
            
            # 扣除内圈（黑色）- 保护中心纹理
            cv2.circle(mask, center, inner_radius, 0, -1)
        
        # 高斯模糊使边缘过渡更自然
        mask = cv2.GaussianBlur(mask, (7, 7), 0)
        
        return mask
    
    def generate_full_eye_mask(
        self,
        image: np.ndarray,
        detection_result: EyeDetectionResult,
        expand_pixels: int = 5
    ) -> np.ndarray:
        """
        生成完整眼球区域蒙版
        
        Args:
            image: 原始图像
            detection_result: 眼球检测结果
            expand_pixels: 边缘扩展像素
            
        Returns:
            蒙版图像
        """
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        for eye_data in [detection_result.left_eye, detection_result.right_eye]:
            if eye_data is None:
                continue
            
            radius = int(eye_data.radius + expand_pixels)
            cv2.circle(mask, eye_data.center_px, radius, 255, -1)
        
        # 轻微模糊边缘
        mask = cv2.GaussianBlur(mask, (5, 5), 0)
        
        return mask
    
    def _image_to_base64(self, image: np.ndarray) -> str:
        """将OpenCV图像转换为base64字符串"""
        success, buffer = cv2.imencode('.png', image)
        if not success:
            raise ValueError("图像编码失败")
        return base64.b64encode(buffer).decode('utf-8')
    
    def _base64_to_image(self, base64_str: str) -> np.ndarray:
        """将base64字符串转换为OpenCV图像"""
        img_data = base64.b64decode(base64_str)
        img_array = np.frombuffer(img_data, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    def refine_with_api(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        denoising_strength: float = 0.35,
        prompt: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        steps: int = 25,
        cfg_scale: float = 7.0,
        sampler_name: str = "DPM++ 2M Karras"
    ) -> np.ndarray:
        """
        使用Automatic1111 WebUI API进行Inpainting
        
        Args:
            image: 输入图像 (BGR)
            mask: Inpainting蒙版 (白色=重绘区域)
            denoising_strength: 重绘强度 (0.3-0.4推荐，保护纹理)
            prompt: 正向提示词
            negative_prompt: 反向提示词
            steps: 采样步数
            cfg_scale: CFG强度
            sampler_name: 采样器名称
            
        Returns:
            处理后的图像
        """
        if prompt is None:
            prompt = self.default_prompt
        if negative_prompt is None:
            negative_prompt = self.default_negative_prompt
        
        # 准备API请求
        payload = {
            "init_images": [self._image_to_base64(image)],
            "mask": self._image_to_base64(mask),
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "denoising_strength": denoising_strength,
            "sampler_name": sampler_name,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": image.shape[1],
            "height": image.shape[0],
            "mask_blur": 4,
            "inpainting_fill": 1,  # 1 = original content
            "inpaint_full_res": True,
            "inpaint_full_res_padding": 32,
        }
        
        try:
            print(f"    正在调用SD API ({self.api_url})...")
            response = requests.post(
                f"{self.api_url}/sdapi/v1/img2img",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            if 'images' in result and len(result['images']) > 0:
                print("    SD处理完成")
                return self._base64_to_image(result['images'][0])
            else:
                print("    警告: API未返回图像")
                return image
                
        except requests.exceptions.ConnectionError:
            print(f"    错误: 无法连接到SD WebUI API ({self.api_url})")
            print("    请确保Stable Diffusion WebUI已启动并开启了API (--api 参数)")
            return image
            
        except requests.exceptions.Timeout:
            print(f"    错误: API请求超时 ({self.timeout}秒)")
            return image
            
        except requests.exceptions.RequestException as e:
            print(f"    API调用失败: {e}")
            return image
    
    def refine(
        self,
        image: np.ndarray,
        detection_result: EyeDetectionResult,
        denoising_strength: float = 0.35,
        expand_pixels: int = 5,
        protect_center: bool = True,
        protect_center_ratio: float = 0.65
    ) -> np.ndarray:
        """
        完整的融合流程
        
        Args:
            image: 已贴上美瞳的图像
            detection_result: 眼球检测结果
            denoising_strength: 重绘强度 (0.2-0.4推荐)
            expand_pixels: 蒙版外扩像素
            protect_center: 是否保护中心纹理（只处理边缘）
            protect_center_ratio: 保护中心区域比例
            
        Returns:
            融合后的图像
        """
        # 检查API可用性
        if not self.check_api_available():
            print("    警告: SD WebUI API不可用，跳过融合步骤")
            return image
        
        # 生成蒙版
        if protect_center:
            mask = self.generate_edge_mask(
                image, 
                detection_result, 
                expand_pixels,
                protect_center_ratio=protect_center_ratio
            )
        else:
            mask = self.generate_full_eye_mask(
                image, 
                detection_result, 
                expand_pixels
            )
        
        # 调用SD Inpainting
        result = self.refine_with_api(image, mask, denoising_strength)
        
        return result
    
    def preview_mask(
        self,
        image: np.ndarray,
        mask: np.ndarray
    ) -> np.ndarray:
        """
        预览蒙版覆盖效果（用于调试）
        
        Args:
            image: 原始图像
            mask: 蒙版
            
        Returns:
            带蒙版叠加的预览图
        """
        preview = image.copy()
        
        # 创建红色蒙版叠加
        red_overlay = np.zeros_like(preview)
        red_overlay[:, :, 2] = mask  # 红色通道
        
        # 混合
        alpha = 0.5
        preview = cv2.addWeighted(preview, 1, red_overlay, alpha, 0)
        
        return preview


class LocalInpaintRefiner:
    """
    本地Inpainting处理器 (不依赖SD API)
    使用OpenCV的inpaint函数进行简单修复
    """
    
    def __init__(self):
        pass
    
    def refine(
        self,
        image: np.ndarray,
        detection_result: EyeDetectionResult,
        expand_pixels: int = 3,
        inpaint_radius: int = 3
    ) -> np.ndarray:
        """
        使用OpenCV inpaint进行简单边缘修复
        
        注意: 效果不如SD Inpainting，但不需要额外依赖
        """
        h, w = image.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # 只在边缘画细环
        for eye_data in [detection_result.left_eye, detection_result.right_eye]:
            if eye_data is None:
                continue
            
            radius = int(eye_data.radius)
            # 画细环
            cv2.circle(mask, eye_data.center_px, radius + expand_pixels, 255, 3)
        
        # 使用Telea算法修复
        result = cv2.inpaint(image, mask, inpaint_radius, cv2.INPAINT_TELEA)
        
        return result


if __name__ == "__main__":
    import sys
    from iris_detector import IrisDetector
    
    if len(sys.argv) < 2:
        print("用法: python sd_refiner.py <图片路径> [--check-api]")
        sys.exit(1)
    
    if sys.argv[1] == "--check-api":
        refiner = SDInpaintingRefiner()
        if refiner.check_api_available():
            print("✓ SD WebUI API 可用")
        else:
            print("✗ SD WebUI API 不可用")
            print(f"  请确保 Stable Diffusion WebUI 已启动")
            print(f"  启动命令: python launch.py --api")
        sys.exit(0)
    
    image_path = sys.argv[1]
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"无法读取图像: {image_path}")
        sys.exit(1)
    
    # 检测眼睛
    detector = IrisDetector()
    result = detector.detect(image)
    detector.close()
    
    if not result.success:
        print("未检测到人脸")
        sys.exit(1)
    
    # 生成蒙版预览
    refiner = SDInpaintingRefiner()
    
    # 生成边缘蒙版
    edge_mask = refiner.generate_edge_mask(image, result)
    
    # 预览
    preview = refiner.preview_mask(image, edge_mask)
    
    cv2.imshow("Edge Mask Preview (red = inpaint area)", preview)
    cv2.imshow("Edge Mask", edge_mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
