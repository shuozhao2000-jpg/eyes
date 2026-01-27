"""
交互式手动定位工具
- 鼠标左键点击：设置圆心位置
- 滚轮上/下：增大/减小半径
- 按 'S' 键：保存当前设置并退出
- 按 'Q' 键：不保存退出
- 按 'R' 键：重置
"""
import cv2
import numpy as np

# 全局变量
cx, cy = 644, 654
radius = 50
img_original = None
img_display = None

def mouse_callback(event, x, y, flags, param):
    global cx, cy, radius, img_display
    
    if event == cv2.EVENT_LBUTTONDOWN:
        # 左键点击设置圆心（需要转换回原图坐标）
        # 显示窗口是放大的，需要计算实际坐标
        scale = param['scale']
        offset_x = param['offset_x']
        offset_y = param['offset_y']
        
        cx = int(x / scale) + offset_x
        cy = int(y / scale) + offset_y
        update_display(param)
        
    elif event == cv2.EVENT_MOUSEWHEEL:
        # 滚轮调整半径
        if flags > 0:
            radius += 2
        else:
            radius = max(5, radius - 2)
        update_display(param)

def update_display(param):
    global img_display
    
    offset_x = param['offset_x']
    offset_y = param['offset_y']
    crop_w = param['crop_w']
    crop_h = param['crop_h']
    scale = param['scale']
    
    # 裁剪区域
    crop = img_original[offset_y:offset_y+crop_h, offset_x:offset_x+crop_w].copy()
    
    # 画圆圈
    rel_cx = cx - offset_x
    rel_cy = cy - offset_y
    cv2.circle(crop, (rel_cx, rel_cy), radius, (0, 255, 0), 2)
    cv2.circle(crop, (rel_cx, rel_cy), 3, (0, 0, 255), -1)
    
    # 放大
    display_w = int(crop_w * scale)
    display_h = int(crop_h * scale)
    img_display = cv2.resize(crop, (display_w, display_h), interpolation=cv2.INTER_CUBIC)
    
    # 添加文字说明
    cv2.putText(img_display, f"Center: ({cx}, {cy})", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img_display, f"Radius: {radius}", (10, 60), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(img_display, "[Click] Set center  [Scroll] Adjust radius", (10, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    cv2.putText(img_display, "[S] Save & Exit  [Q] Quit  [R] Reset", (10, 115), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)


def main():
    global img_original, cx, cy, radius
    
    print("=" * 50)
    print("  Interactive Eye Region Selector")
    print("=" * 50)
    print("\nControls:")
    print("  - Left Click: Set center position")
    print("  - Mouse Wheel: Adjust radius")
    print("  - S: Save settings and exit")
    print("  - Q: Quit without saving")
    print("  - R: Reset to default")
    print()
    
    # 加载图片
    img_original = cv2.imread('output/result_coral_brown.jpg')
    if img_original is None:
        print("Error: Cannot load image!")
        return
    
    # 裁剪参数（右下角眼睛区域）
    param = {
        'offset_x': 560,
        'offset_y': 550,
        'crop_w': 200,
        'crop_h': 170,
        'scale': 2.5
    }
    
    # 创建窗口
    window_name = 'Select Eye Region (S=Save, Q=Quit)'
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback, param)
    
    # 初始显示
    update_display(param)
    
    saved = False
    while True:
        cv2.imshow(window_name, img_display)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s') or key == ord('S'):
            # 保存设置
            saved = True
            break
        elif key == ord('q') or key == ord('Q'):
            break
        elif key == ord('r') or key == ord('R'):
            # 重置
            cx, cy = 644, 654
            radius = 50
            update_display(param)
    
    cv2.destroyAllWindows()
    
    if saved:
        print(f"\n[SAVED] Settings:")
        print(f"  CLEAR_CX = {cx}")
        print(f"  CLEAR_CY = {cy}")
        print(f"  CLEAR_RADIUS = {radius}")
        
        # 保存预览图
        preview = img_display.copy()
        cv2.imwrite('output/clear_preview.jpg', preview)
        print("\n[PREVIEW] Saved: output/clear_preview.jpg")
        
        # 写入配置文件供其他脚本使用
        with open('output/clear_config.txt', 'w') as f:
            f.write(f"{cx},{cy},{radius}")
        print("[CONFIG] Saved: output/clear_config.txt")
    else:
        print("\n[CANCELLED] No changes saved.")


if __name__ == "__main__":
    main()
