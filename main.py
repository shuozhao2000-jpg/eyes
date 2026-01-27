"""
美瞳替换工具 - 主程序
将美瞳素材精准贴合到模特眼睛上，保留颜色和纹理
"""

import cv2
import numpy as np
import argparse
import os
from pathlib import Path

from iris_detector import IrisDetector, EyeDetectionResult
from lens_overlay import ContactLensOverlay, extract_lens_from_eye_image
from sd_refiner import SDInpaintingRefiner, LocalInpaintRefiner


def replace_contact_lens(
    model_image_path: str,
    lens_image_path: str,
    output_path: str,
    use_sd_refinement: bool = True,
    sd_api_url: str = "http://127.0.0.1:7860",
    denoising_strength: float = 0.35,
    preserve_highlights: bool = True,
    highlight_threshold: int = 220,
    blend_mode: str = "normal",
    opacity: float = 1.0,
    protect_center: bool = True,
    show_preview: bool = False
) -> np.ndarray:
    """
    完整的美瞳替换流程
    
    Args:
        model_image_path: 模特照片路径
        lens_image_path: 美瞳PNG图片路径 (需要透明通道)
        output_path: 输出图片路径
        use_sd_refinement: 是否使用SD进行边缘融合
        sd_api_url: SD WebUI API地址
        denoising_strength: SD重绘强度 (0.2-0.4推荐)
        preserve_highlights: 是否保留高光
        highlight_threshold: 高光阈值 (0-255)
        blend_mode: 混合模式 ("normal", "soft_light", "overlay")
        opacity: 不透明度 (0.0-1.0)
        protect_center: SD融合时是否保护中心纹理
        show_preview: 是否显示预览窗口
        
    Returns:
        处理后的图像
    """
    print("=" * 60)
    print("  美瞳替换工具 v1.0")
    print("  精准贴合 | 保留颜色 | 保留纹理")
    print("=" * 60)
    
    # ========== 1. 读取图像 ==========
    print("\n[1/5] 读取图像...")
    
    model_image = cv2.imread(model_image_path)
    if model_image is None:
        raise ValueError(f"无法读取模特图片: {model_image_path}")
    
    h, w = model_image.shape[:2]
    print(f"      模特图片: {model_image_path}")
    print(f"      尺寸: {w}x{h}")
    
    # ========== 2. 检测眼球 ==========
    print("\n[2/5] 检测眼球关键点...")
    
    detector = IrisDetector()
    detection_result = detector.detect(model_image)
    
    if not detection_result.success:
        detector.close()
        raise ValueError("未检测到人脸或眼球，请确保图片中有清晰的正面人脸")
    
    if detection_result.left_eye:
        le = detection_result.left_eye
        print(f"      左眼: 中心{le.center_px}, 半径{le.radius:.1f}px")
        pitch, yaw, roll = le.euler_angles
        print(f"            角度(pitch={pitch:.2f}, yaw={yaw:.2f})")
    
    if detection_result.right_eye:
        re = detection_result.right_eye
        print(f"      右眼: 中心{re.center_px}, 半径{re.radius:.1f}px")
        pitch, yaw, roll = re.euler_angles
        print(f"            角度(pitch={pitch:.2f}, yaw={yaw:.2f})")
    
    # 保存检测结果可视化（调试用）
    debug_image = detector.draw_landmarks(model_image, detection_result)
    debug_path = str(Path(output_path).parent / "debug_landmarks.jpg")
    cv2.imwrite(debug_path, debug_image)
    print(f"      关键点可视化已保存: {debug_path}")
    
    detector.close()
    
    # ========== 3. 叠加美瞳 ==========
    print("\n[3/5] 叠加美瞳素材...")
    print(f"      美瞳素材: {lens_image_path}")
    print(f"      混合模式: {blend_mode}")
    print(f"      不透明度: {opacity}")
    print(f"      保留高光: {preserve_highlights} (阈值={highlight_threshold})")
    
    overlay = ContactLensOverlay(lens_image_path)
    result = overlay.apply_to_both_eyes(
        model_image, 
        detection_result, 
        preserve_highlights=preserve_highlights,
        highlight_threshold=highlight_threshold,
        blend_mode=blend_mode,
        opacity=opacity
    )
    
    # 保存叠加后的中间结果
    intermediate_path = str(Path(output_path).parent / "intermediate_overlay.jpg")
    cv2.imwrite(intermediate_path, result)
    print(f"      叠加结果已保存: {intermediate_path}")
    
    # ========== 4. SD边缘融合（可选） ==========
    if use_sd_refinement:
        print(f"\n[4/5] SD Inpainting 边缘融合...")
        print(f"      API地址: {sd_api_url}")
        print(f"      重绘强度: {denoising_strength}")
        print(f"      保护中心: {protect_center}")
        
        refiner = SDInpaintingRefiner(api_url=sd_api_url)
        
        if refiner.check_api_available():
            result = refiner.refine(
                result, 
                detection_result,
                denoising_strength=denoising_strength,
                protect_center=protect_center
            )
        else:
            print("      SD API不可用，使用本地修复...")
            local_refiner = LocalInpaintRefiner()
            result = local_refiner.refine(result, detection_result)
    else:
        print("\n[4/5] 跳过SD边缘融合 (use_sd_refinement=False)")
    
    # ========== 5. 保存结果 ==========
    print(f"\n[5/5] 保存最终结果...")
    
    # 确保输出目录存在
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(output_path, result)
    print(f"      输出: {output_path}")
    
    # ========== 完成 ==========
    print("\n" + "=" * 60)
    print("  处理完成!")
    print("=" * 60)
    
    # 显示预览
    if show_preview:
        # 创建对比图
        comparison = np.hstack([model_image, result])
        
        # 缩放以适应屏幕
        max_width = 1400
        if comparison.shape[1] > max_width:
            scale = max_width / comparison.shape[1]
            comparison = cv2.resize(comparison, None, fx=scale, fy=scale)
        
        cv2.imshow("Before / After (按任意键关闭)", comparison)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    return result


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="美瞳替换工具 - 将美瞳素材精准贴合到模特眼睛上",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法
  python main.py model.jpg lens.png output.jpg
  
  # 调整参数
  python main.py model.jpg lens.png output.jpg --opacity 0.8 --blend soft_light
  
  # 禁用SD融合
  python main.py model.jpg lens.png output.jpg --no-sd
  
  # 从眼睛图片提取美瞳纹理
  python main.py --extract eye_photo.jpg lens_extracted.png
        """
    )
    
    # 模式选择
    parser.add_argument(
        "--extract", 
        action="store_true",
        help="提取模式：从眼睛照片中提取美瞳纹理"
    )
    
    # 输入输出
    parser.add_argument(
        "input1",
        help="模特图片路径 (或提取模式下的眼睛图片)"
    )
    parser.add_argument(
        "input2",
        help="美瞳PNG路径 (或提取模式下的输出路径)"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="result.jpg",
        help="输出图片路径 (默认: result.jpg)"
    )
    
    # 叠加参数
    parser.add_argument(
        "--opacity",
        type=float,
        default=1.0,
        help="美瞳不透明度 0.0-1.0 (默认: 1.0)"
    )
    parser.add_argument(
        "--blend",
        choices=["normal", "soft_light", "overlay"],
        default="normal",
        help="混合模式 (默认: normal)"
    )
    parser.add_argument(
        "--no-highlight",
        action="store_true",
        help="不保留高光"
    )
    parser.add_argument(
        "--highlight-threshold",
        type=int,
        default=220,
        help="高光检测阈值 0-255 (默认: 220)"
    )
    
    # SD融合参数
    parser.add_argument(
        "--no-sd",
        action="store_true",
        help="禁用SD Inpainting边缘融合"
    )
    parser.add_argument(
        "--sd-url",
        default="http://127.0.0.1:7860",
        help="SD WebUI API地址 (默认: http://127.0.0.1:7860)"
    )
    parser.add_argument(
        "--denoise",
        type=float,
        default=0.35,
        help="SD重绘强度 0.0-1.0 (默认: 0.35, 推荐0.2-0.4)"
    )
    parser.add_argument(
        "--no-protect-center",
        action="store_true",
        help="SD融合时不保护中心纹理"
    )
    
    # 其他
    parser.add_argument(
        "--preview",
        action="store_true",
        help="处理完成后显示预览窗口"
    )
    
    args = parser.parse_args()
    
    # 提取模式
    if args.extract:
        print("提取模式：从眼睛照片中提取美瞳纹理")
        extract_lens_from_eye_image(args.input1, args.input2)
        return
    
    # 替换模式
    try:
        replace_contact_lens(
            model_image_path=args.input1,
            lens_image_path=args.input2,
            output_path=args.output,
            use_sd_refinement=not args.no_sd,
            sd_api_url=args.sd_url,
            denoising_strength=args.denoise,
            preserve_highlights=not args.no_highlight,
            highlight_threshold=args.highlight_threshold,
            blend_mode=args.blend,
            opacity=args.opacity,
            protect_center=not args.no_protect_center,
            show_preview=args.preview
        )
    except Exception as e:
        print(f"\n错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
