"""
手动圈选要清除为白色的眼球区域
"""
import cv2
import numpy as np

# ============================================
# 调整这些参数来圈选要清除的区域！
# ============================================
CLEAR_CX = 644      # 圆心X
CLEAR_CY = 654      # 圆心Y
CLEAR_RADIUS = 50   # 清除半径
# ============================================


def create_preview(image_path, cx, cy, radius):
    """创建预览图，显示要清除的区域"""
    img = cv2.imread(image_path)
    
    # 裁剪右下角区域
    crop = img[550:720, 560:760].copy()
    
    # 计算在裁剪图中的相对坐标
    rel_cx = cx - 560
    rel_cy = cy - 550
    
    # 画圆圈显示清除范围
    cv2.circle(crop, (rel_cx, rel_cy), radius, (0, 255, 0), 2)
    cv2.circle(crop, (rel_cx, rel_cy), 3, (0, 0, 255), -1)
    
    # 放大显示
    crop_large = cv2.resize(crop, (400, 340), interpolation=cv2.INTER_CUBIC)
    
    # 添加文字
    cv2.putText(crop_large, f"Center: ({cx}, {cy})", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(crop_large, f"Radius: {radius}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(crop_large, "Green circle = area to clear", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return crop_large


if __name__ == "__main__":
    print("=" * 50)
    print("  手动圈选清除区域")
    print("=" * 50)
    print(f"\nCurrent settings:")
    print(f"  Center: ({CLEAR_CX}, {CLEAR_CY})")
    print(f"  Radius: {CLEAR_RADIUS}")
    
    # 创建预览
    preview = create_preview('output/result_coral_brown.jpg', 
                              CLEAR_CX, CLEAR_CY, CLEAR_RADIUS)
    cv2.imwrite('output/clear_preview.jpg', preview)
    print("\n[PREVIEW] Saved: output/clear_preview.jpg")
    print("\nCheck if the green circle covers the entire eye area you want to clear!")
