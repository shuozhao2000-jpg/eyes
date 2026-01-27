"""
交互式定位眼部图 - 上下左右四条边可分别调整

操作说明：
- 鼠标左键点击：设置圆心位置
- 滚轮：调整整体大小
- W 键：上边往上（扩大）
- S 键：上边往下（缩小）
- I 键：下边往下（扩大）
- K 键：下边往上（缩小）
- A 键：左边往左（扩大）
- D 键：左边往右（缩小）
- J 键：右边往左（缩小）
- L 键：右边往右（扩大）
- R 键：重置为圆形
- 空格键：保存并退出
- Q 键：不保存退出
"""
import cv2
import numpy as np

# 全局变量
cx, cy = 451, 242
top = 90      # 上边到圆心的距离
bottom = 110  # 下边到圆心的距离
left = 115    # 左边到圆心的距离
right = 115   # 右边到圆心的距离

img_original = None
img_display = None

def mouse_callback(event, x, y, flags, param):
    global cx, cy, top, bottom, left, right, img_display
    
    scale = param['scale']
    
    if event == cv2.EVENT_LBUTTONDOWN:
        cx = int(x / scale)
        cy = int(y / scale)
        update_display(param)
        
    elif event == cv2.EVENT_MOUSEWHEEL:
        # 滚轮调整整体大小
        delta = 5 if flags > 0 else -5
        top = max(10, top + delta)
        bottom = max(10, bottom + delta)
        left = max(10, left + delta)
        right = max(10, right + delta)
        update_display(param)

def draw_custom_shape(img, cx, cy, top, bottom, left, right, color, thickness):
    """绘制四边可调的不规则形状"""
    points = []
    num_points = 72
    
    for i in range(num_points):
        angle = 2 * np.pi * i / num_points
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        if sin_a < 0:  # 上半部分
            ry = top
        else:  # 下半部分
            ry = bottom
            
        if cos_a < 0:  # 左半部分
            rx = left
        else:  # 右半部分
            rx = right
        
        px = int(cx + rx * cos_a)
        py = int(cy + ry * sin_a)
        points.append([px, py])
    
    points = np.array(points, dtype=np.int32)
    cv2.polylines(img, [points], True, color, thickness)
    return points

def update_display(param):
    global img_display
    
    scale = param['scale']
    
    display = img_original.copy()
    
    # 画自定义形状
    draw_custom_shape(display, cx, cy, top, bottom, left, right, (0, 255, 0), 2)
    
    # 画圆心
    cv2.circle(display, (cx, cy), 3, (0, 0, 255), -1)
    
    # 画四条边的标记线
    cv2.line(display, (cx, cy - top), (cx, cy - top - 20), (0, 255, 255), 2)  # 上（黄）
    cv2.line(display, (cx, cy + bottom), (cx, cy + bottom + 20), (255, 0, 255), 2)  # 下（紫）
    cv2.line(display, (cx - left, cy), (cx - left - 20, cy), (255, 255, 0), 2)  # 左（青）
    cv2.line(display, (cx + right, cy), (cx + right + 20, cy), (0, 165, 255), 2)  # 右（橙）
    
    # 缩放显示
    h, w = display.shape[:2]
    display_w = int(w * scale)
    display_h = int(h * scale)
    img_display = cv2.resize(display, (display_w, display_h), interpolation=cv2.INTER_CUBIC)
    
    # 添加中文说明（用英文显示，因为OpenCV不支持中文）
    cv2.putText(img_display, f"Center: ({cx}, {cy})", (10, 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(img_display, f"Shang(Top): {top}    Xia(Bottom): {bottom}", (10, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(img_display, f"Zuo(Left): {left}    You(Right): {right}", (10, 75), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(img_display, "[W/S] Shang bian  [I/K] Xia bian", (10, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv2.putText(img_display, "[A/D] Zuo bian    [J/L] You bian", (10, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    cv2.putText(img_display, "[Click] Zhongxin [Scroll] Zhengti [R] Chongzhi", (10, 140), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
    cv2.putText(img_display, "[SPACE] Baocun tuichu  [Q] Quxiao", (10, 160), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)


def main():
    global img_original, cx, cy, top, bottom, left, right
    
    print("=" * 50)
    print("  交互式定位工具 - 上下左右四边可调")
    print("=" * 50)
    print("\n操作说明：")
    print("  鼠标左键点击：设置圆心位置")
    print("  滚轮：调整整体大小")
    print("  W 键：上边往上（扩大）")
    print("  S 键：上边往下（缩小）")
    print("  I 键：下边往下（扩大）")
    print("  K 键：下边往上（缩小）")
    print("  A 键：左边往左（扩大）")
    print("  D 键：左边往右（缩小）")
    print("  J 键：右边往左（缩小）")
    print("  L 键：右边往右（扩大）")
    print("  R 键：重置为圆形")
    print("  空格键：保存并退出")
    print("  Q 键：不保存退出")
    print()
    
    img_original = cv2.imread('input/source_eye.jpg')
    if img_original is None:
        print("Error: Cannot load input/source_eye.jpg!")
        return
    
    param = {'scale': 0.8}
    
    window_name = 'Dingwei Gongju (SPACE=Baocun, Q=Tuichu)'
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback, param)
    
    update_display(param)
    
    saved = False
    while True:
        cv2.imshow(window_name, img_display)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            saved = True
            break
        elif key == ord('q') or key == ord('Q'):
            break
        elif key == ord('r') or key == ord('R'):
            avg = (top + bottom + left + right) // 4
            top = bottom = left = right = avg
            update_display(param)
        # W/S - 调整上边
        elif key == ord('w') or key == ord('W'):
            top += 3
            update_display(param)
        elif key == ord('s') or key == ord('S'):
            top = max(10, top - 3)
            update_display(param)
        # I/K - 调整下边
        elif key == ord('i') or key == ord('I'):
            bottom += 3
            update_display(param)
        elif key == ord('k') or key == ord('K'):
            bottom = max(10, bottom - 3)
            update_display(param)
        # A/D - 调整左边
        elif key == ord('a') or key == ord('A'):
            left += 3
            update_display(param)
        elif key == ord('d') or key == ord('D'):
            left = max(10, left - 3)
            update_display(param)
        # J/L - 调整右边
        elif key == ord('j') or key == ord('J'):
            right = max(10, right - 3)
            update_display(param)
        elif key == ord('l') or key == ord('L'):
            right += 3
            update_display(param)
    
    cv2.destroyAllWindows()
    
    if saved:
        print(f"\n[已保存] 设置：")
        print(f"  圆心 = ({cx}, {cy})")
        print(f"  上边 = {top}")
        print(f"  下边 = {bottom}")
        print(f"  左边 = {left}")
        print(f"  右边 = {right}")
        
        cv2.imwrite('output/source_preview.jpg', img_display)
        print("\n[预览图] 已保存: output/source_preview.jpg")
        
        with open('output/source_config.txt', 'w') as f:
            f.write(f"{cx},{cy},{top},{bottom},{left},{right}")
        print("[配置文件] 已保存: output/source_config.txt")
    else:
        print("\n[已取消] 未保存任何更改。")


if __name__ == "__main__":
    main()
