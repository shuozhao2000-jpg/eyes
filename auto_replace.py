"""
一键美瞳替换自动化脚本
只需将图片放入指定位置，运行此脚本即可完成全部流程
"""

import os
import sys
import glob
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from iris_detector import IrisDetector
from lens_overlay import ContactLensOverlay, extract_lens_from_eye_image
from sd_refiner import SDInpaintingRefiner
import cv2
import numpy as np


def find_images(directory: str) -> dict:
    """查找目录中的图片文件"""
    extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.webp']
    images = []
    
    for ext in extensions:
        images.extend(glob.glob(os.path.join(directory, ext)))
        images.extend(glob.glob(os.path.join(directory, ext.upper())))
    
    return sorted(set(images))


def auto_replace():
    """自动化替换流程"""
    
    print("=" * 60)
    print("  美瞳替换自动化工具")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    
    # 创建目录
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 检查输入文件
    source_eye = input_dir / "source_eye.jpg"  # 美瞳效果图（用于提取）
    source_eye_alt = list(input_dir.glob("source_eye.*"))
    
    model_image = input_dir / "model.jpg"  # 模特照片
    model_image_alt = list(input_dir.glob("model.*"))
    
    lens_image = input_dir / "lens.png"  # 美瞳素材（可选，如果没有会自动提取）
    lens_image_alt = list(input_dir.glob("lens.*"))
    
    # 查找实际文件
    source_file = None
    model_file = None
    lens_file = None
    
    # 查找source_eye
    if source_eye.exists():
        source_file = source_eye
    elif source_eye_alt:
        source_file = source_eye_alt[0]
    
    # 查找model
    if model_image.exists():
        model_file = model_image
    elif model_image_alt:
        model_file = model_image_alt[0]
    
    # 查找lens
    if lens_image.exists():
        lens_file = lens_image
    elif lens_image_alt:
        lens_file = lens_image_alt[0]
    
    # 显示状态
    print(f"\n[DIR] 输入目录: {input_dir}")
    print(f"[DIR] 输出目录: {output_dir}")
    print()
    print("[CHECK] 文件检查:")
    print(f"   source_eye (美瞳效果图): {'[OK] ' + str(source_file.name) if source_file else '[X] 未找到'}")
    print(f"   model (模特照片):        {'[OK] ' + str(model_file.name) if model_file else '[X] 未找到'}")
    print(f"   lens (美瞳素材PNG):      {'[OK] ' + str(lens_file.name) if lens_file else '[!] 未找到，将自动提取'}")
    print()
    
    # 检查必需文件
    if not model_file:
        print("[ERROR] 请将模特照片放入 input 文件夹，命名为 model.jpg")
        print(f"   路径: {input_dir}")
        return False
    
    if not source_file and not lens_file:
        print("[ERROR] 请至少提供以下之一:")
        print("   1. source_eye.jpg - 美瞳效果图（会自动提取美瞳纹理）")
        print("   2. lens.png - 美瞳素材PNG（带透明通道）")
        print(f"   路径: {input_dir}")
        return False
    
    # ========== 步骤1: 提取美瞳（如果需要）==========
    if not lens_file and source_file:
        print("\n" + "=" * 60)
        print("[1/3] 从效果图中提取美瞳纹理...")
        print("=" * 60)
        
        lens_file = output_dir / "extracted_lens.png"
        
        try:
            extract_lens_from_eye_image(str(source_file), str(lens_file), expand_ratio=1.3)
            print(f"[OK] 美瞳纹理已提取: {lens_file}")
        except Exception as e:
            print(f"[ERROR] 提取失败: {e}")
            return False
    else:
        print("\n[1/3] 跳过提取（已有美瞳素材）")
    
    # ========== 步骤2: 检测眼球 ==========
    print("\n" + "=" * 60)
    print("[2/3] 检测模特眼球位置...")
    print("=" * 60)
    
    model_img = cv2.imread(str(model_file))
    if model_img is None:
        print(f"[ERROR] 无法读取模特图片: {model_file}")
        return False
    
    detector = IrisDetector()
    detection_result = detector.detect(model_img)
    
    if not detection_result.success:
        print("[ERROR] 未检测到人脸或眼球")
        detector.close()
        return False
    
    # 保存检测可视化
    debug_img = detector.draw_landmarks(model_img, detection_result)
    debug_path = output_dir / "debug_landmarks.jpg"
    cv2.imwrite(str(debug_path), debug_img)
    print(f"[OK] 关键点可视化: {debug_path}")
    
    if detection_result.left_eye:
        le = detection_result.left_eye
        print(f"   左眼: 中心{le.center_px}, 半径{le.radius:.1f}px")
    if detection_result.right_eye:
        re = detection_result.right_eye
        print(f"   右眼: 中心{re.center_px}, 半径{re.radius:.1f}px")
    
    detector.close()
    
    # ========== 步骤3: 叠加美瞳 ==========
    print("\n" + "=" * 60)
    print("[3/3] 叠加美瞳...")
    print("=" * 60)
    
    try:
        overlay = ContactLensOverlay(str(lens_file))
    except Exception as e:
        print(f"[ERROR] 加载美瞳素材失败: {e}")
        return False
    
    # 生成多个版本
    results = []
    
    # 版本1: 正常模式
    result_normal = overlay.apply_to_both_eyes(
        model_img, detection_result,
        preserve_highlights=True,
        highlight_threshold=220,
        blend_mode="normal",
        opacity=1.0
    )
    normal_path = output_dir / "result_normal.jpg"
    cv2.imwrite(str(normal_path), result_normal)
    results.append(("正常模式", normal_path))
    
    # 版本2: 柔光模式
    result_soft = overlay.apply_to_both_eyes(
        model_img, detection_result,
        preserve_highlights=True,
        highlight_threshold=220,
        blend_mode="soft_light",
        opacity=0.9
    )
    soft_path = output_dir / "result_soft_light.jpg"
    cv2.imwrite(str(soft_path), result_soft)
    results.append(("柔光模式", soft_path))
    
    # 版本3: 80%不透明度
    result_80 = overlay.apply_to_both_eyes(
        model_img, detection_result,
        preserve_highlights=True,
        highlight_threshold=220,
        blend_mode="normal",
        opacity=0.8
    )
    opacity_path = output_dir / "result_opacity80.jpg"
    cv2.imwrite(str(opacity_path), result_80)
    results.append(("80%不透明度", opacity_path))
    
    print("\n[OK] 生成了多个版本供你选择:")
    for name, path in results:
        print(f"   - {name}: {path.name}")
    
    # 创建对比图
    h, w = model_img.shape[:2]
    comparison = np.hstack([
        cv2.resize(model_img, (w//2, h//2)),
        cv2.resize(result_normal, (w//2, h//2))
    ])
    comparison_path = output_dir / "comparison.jpg"
    cv2.imwrite(str(comparison_path), comparison)
    print(f"\n[COMPARE] 对比图: {comparison_path}")
    
    # ========== 完成 ==========
    print("\n" + "=" * 60)
    print("  [DONE] 处理完成!")
    print("=" * 60)
    print(f"\n[DIR] 所有结果保存在: {output_dir}")
    print("\n[TIP] 提示:")
    print("   - 如果颜色不对，检查 lens.png 素材")
    print("   - 如果位置不准，检查 debug_landmarks.jpg")
    print("   - 可以尝试不同版本的结果")
    
    return True


def setup_folders():
    """创建输入输出文件夹并显示说明"""
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    output_dir = base_dir / "output"
    
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # 创建说明文件
    readme = input_dir / "请把图片放在这里.txt"
    if not readme.exists():
        readme.write_text("""
美瞳替换工具 - 输入文件说明
============================

请将以下文件放入此文件夹:

1. model.jpg (必需)
   - 模特照片
   - 需要正面清晰的人脸

2. source_eye.jpg (二选一)
   - 美瞳效果展示图
   - 程序会自动从中提取美瞳纹理

3. lens.png (二选一)
   - 美瞳素材PNG
   - 需要带透明通道
   - 如果有这个文件，会跳过提取步骤

文件放好后，运行:
    python auto_replace.py

""", encoding='utf-8')
    
    print(f"[DIR] 输入文件夹已创建: {input_dir}")
    print(f"[DIR] 输出文件夹已创建: {output_dir}")
    print(f"\n请将图片放入 input 文件夹后重新运行此脚本")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input"
    
    # 检查input文件夹是否存在且有文件
    if not input_dir.exists() or not any(input_dir.iterdir()):
        setup_folders()
    else:
        success = auto_replace()
        if not success:
            print("\n处理未完成，请检查上述错误信息")
