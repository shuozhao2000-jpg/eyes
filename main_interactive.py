"""
美瞳替换工具 - 完整交互式版本

功能流程：
1. 定位源图片中的美瞳区域（四边可调）
2. 定位目标图片中的眼球区域
3. 提取美瞳纹理
4. 贴到目标位置
5. 预览和保存结果
"""
import cv2
import numpy as np
import os

# ============================================
# 全局配置
# ============================================
INPUT_SOURCE = 'input/source_eye.jpg'      # 源眼部图
INPUT_TARGET = 'output/result_coral_brown.jpg'  # 目标图片
OUTPUT_DIR = 'output'

# 源图片定位参数
source_cx, source_cy = 451, 242
source_top, source_bottom = 96, 131
source_left, source_right = 130, 127
source_feather = 30

# 目标图片定位参数
target_cx, target_cy = 644, 654
target_radius = 34


def step1_locate_source():
    """步骤1：定位源图片中的美瞳区域"""
    global source_cx, source_cy, source_top, source_bottom, source_left, source_right
    
    print("\n" + "=" * 50)
    print("  步骤1：定位源图片中的美瞳区域")
    print("=" * 50)
    print("\n操作说明：")
    print("  鼠标左键点击：设置圆心位置")
    print("  滚轮：调整整体大小")
    print("  W/S 键：上边 往上/往下")
    print("  I/K 键：下边 往下/往上")
    print("  A/D 键：左边 往左/往右")
    print("  J/L 键：右边 往左/往右")
    print("  R 键：重置为圆形")
    print("  空格键：确认并继续")
    print("  Q 键：退出程序")
    
    img = cv2.imread(INPUT_SOURCE)
    if img is None:
        print(f"错误：无法加载 {INPUT_SOURCE}")
        return False
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal source_cx, source_cy, source_top, source_bottom, source_left, source_right
        scale = 0.8
        if event == cv2.EVENT_LBUTTONDOWN:
            source_cx = int(x / scale)
            source_cy = int(y / scale)
        elif event == cv2.EVENT_MOUSEWHEEL:
            delta = 5 if flags > 0 else -5
            source_top = max(10, source_top + delta)
            source_bottom = max(10, source_bottom + delta)
            source_left = max(10, source_left + delta)
            source_right = max(10, source_right + delta)
    
    def update_display():
        display = img.copy()
        # 画四边可调的形状
        points = []
        for i in range(72):
            angle = 2 * np.pi * i / 72
            cos_a, sin_a = np.cos(angle), np.sin(angle)
            ry = source_top if sin_a < 0 else source_bottom
            rx = source_left if cos_a < 0 else source_right
            points.append([int(source_cx + rx * cos_a), int(source_cy + ry * sin_a)])
        cv2.polylines(display, [np.array(points, dtype=np.int32)], True, (0, 255, 0), 2)
        cv2.circle(display, (source_cx, source_cy), 3, (0, 0, 255), -1)
        
        # 缩放显示
        h, w = display.shape[:2]
        display = cv2.resize(display, (int(w * 0.8), int(h * 0.8)))
        
        # 添加说明
        cv2.putText(display, f"Center: ({source_cx}, {source_cy})", (10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(display, f"T:{source_top} B:{source_bottom} L:{source_left} R:{source_right}", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(display, "[W/S]Shang [I/K]Xia [A/D]Zuo [J/L]You", (10, 75), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        cv2.putText(display, "[SPACE]Queren [Q]Tuichu", (10, 95), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        return display
    
    window = 'Step1: Dingwei Meintong (SPACE=Queren)'
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, mouse_callback)
    
    while True:
        cv2.imshow(window, update_display())
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            cv2.destroyAllWindows()
            return True
        elif key == ord('q') or key == ord('Q'):
            cv2.destroyAllWindows()
            return False
        elif key == ord('w') or key == ord('W'):
            source_top += 3
        elif key == ord('s') or key == ord('S'):
            source_top = max(10, source_top - 3)
        elif key == ord('i') or key == ord('I'):
            source_bottom += 3
        elif key == ord('k') or key == ord('K'):
            source_bottom = max(10, source_bottom - 3)
        elif key == ord('a') or key == ord('A'):
            source_left += 3
        elif key == ord('d') or key == ord('D'):
            source_left = max(10, source_left - 3)
        elif key == ord('j') or key == ord('J'):
            source_right = max(10, source_right - 3)
        elif key == ord('l') or key == ord('L'):
            source_right += 3
        elif key == ord('r') or key == ord('R'):
            avg = (source_top + source_bottom + source_left + source_right) // 4
            source_top = source_bottom = source_left = source_right = avg


def step2_locate_target():
    """步骤2：定位目标图片中的眼球区域"""
    global target_cx, target_cy, target_radius
    
    print("\n" + "=" * 50)
    print("  步骤2：定位目标图片中的眼球区域")
    print("=" * 50)
    print("\n操作说明：")
    print("  鼠标左键点击：设置圆心位置")
    print("  滚轮：调整半径大小")
    print("  空格键：确认并继续")
    print("  Q 键：退出程序")
    
    img = cv2.imread(INPUT_TARGET)
    if img is None:
        print(f"错误：无法加载 {INPUT_TARGET}")
        return False
    
    # 裁剪右下角区域
    crop_x1, crop_y1 = 560, 550
    crop_x2, crop_y2 = 760, 720
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal target_cx, target_cy, target_radius
        scale = 2.5
        if event == cv2.EVENT_LBUTTONDOWN:
            target_cx = int(x / scale) + crop_x1
            target_cy = int(y / scale) + crop_y1
        elif event == cv2.EVENT_MOUSEWHEEL:
            target_radius = max(5, target_radius + (2 if flags > 0 else -2))
    
    def update_display():
        crop = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()
        rel_cx = target_cx - crop_x1
        rel_cy = target_cy - crop_y1
        cv2.circle(crop, (rel_cx, rel_cy), target_radius, (0, 255, 0), 2)
        cv2.circle(crop, (rel_cx, rel_cy), 3, (0, 0, 255), -1)
        
        # 放大显示
        display = cv2.resize(crop, (int(crop.shape[1] * 2.5), int(crop.shape[0] * 2.5)))
        
        cv2.putText(display, f"Center: ({target_cx}, {target_cy})", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, f"Radius: {target_radius}", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(display, "[Click]Zhongxin [Scroll]Banjing", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(display, "[SPACE]Queren [Q]Tuichu", (10, 115), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        return display
    
    window = 'Step2: Dingwei Mubiao Yanqiu (SPACE=Queren)'
    cv2.namedWindow(window)
    cv2.setMouseCallback(window, mouse_callback)
    
    while True:
        cv2.imshow(window, update_display())
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            cv2.destroyAllWindows()
            return True
        elif key == ord('q') or key == ord('Q'):
            cv2.destroyAllWindows()
            return False


def step3_extract_and_apply():
    """步骤3：提取纹理并应用到目标"""
    print("\n" + "=" * 50)
    print("  步骤3：提取纹理并应用")
    print("=" * 50)
    
    # 提取纹理
    print("\n正在提取美瞳纹理...")
    img_source = cv2.imread(INPUT_SOURCE)
    
    max_r = max(source_top, source_bottom, source_left, source_right)
    x1 = max(0, source_cx - max_r)
    y1 = max(0, source_cy - max_r)
    x2 = min(img_source.shape[1], source_cx + max_r)
    y2 = min(img_source.shape[0], source_cy + max_r)
    
    cropped = img_source[y1:y2, x1:x2].copy()
    ch, cw = cropped.shape[:2]
    center_x = source_cx - x1
    center_y = source_cy - y1
    
    # 创建Alpha蒙版
    alpha = np.zeros((ch, cw), dtype=np.float32)
    for y in range(ch):
        for x in range(cw):
            dx, dy = x - center_x, y - center_y
            ry = source_top if dy < 0 else source_bottom
            rx = source_left if dx < 0 else source_right
            if rx > 0 and ry > 0:
                dist = np.sqrt((dx / rx)**2 + (dy / ry)**2)
                if dist <= 1:
                    if dist > 1 - source_feather / max(rx, ry):
                        alpha[y, x] = (1 - dist) / (source_feather / max(rx, ry))
                    else:
                        alpha[y, x] = 1.0
    
    alpha = (alpha * 255).astype(np.uint8)
    texture = np.dstack([cropped, alpha])
    
    cv2.imwrite(f'{OUTPUT_DIR}/extracted_texture.png', texture)
    print(f"  已保存: {OUTPUT_DIR}/extracted_texture.png")
    
    # 应用到目标
    print("\n正在应用纹理到目标...")
    img_target = cv2.imread(INPUT_TARGET)
    
    # 计算缩放
    th, tw = texture.shape[:2]
    texture_radius = min(th, tw) // 2
    scale = (target_radius / texture_radius) * 1.1
    
    new_w, new_h = int(tw * scale), int(th * scale)
    scaled = cv2.resize(texture, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # 计算叠加位置
    px1 = target_cx - new_w // 2
    py1 = target_cy - new_h // 2
    px2, py2 = px1 + new_w, py1 + new_h
    
    ox1, oy1, ox2, oy2 = 0, 0, new_w, new_h
    bh, bw = img_target.shape[:2]
    
    if px1 < 0: ox1, px1 = -px1, 0
    if py1 < 0: oy1, py1 = -py1, 0
    if px2 > bw: ox2, px2 = ox2 - (px2 - bw), bw
    if py2 > bh: oy2, py2 = oy2 - (py2 - bh), bh
    
    overlay_roi = scaled[oy1:oy2, ox1:ox2]
    base_roi = img_target[py1:py2, px1:px2].astype(float)
    
    overlay_bgr = overlay_roi[:, :, :3].astype(float)
    overlay_alpha = overlay_roi[:, :, 3:4].astype(float) / 255.0
    
    # 排除源纹理高光
    overlay_gray = cv2.cvtColor(overlay_roi[:, :, :3], cv2.COLOR_BGR2GRAY)
    source_highlight = (overlay_gray > 220).astype(float)
    source_highlight = cv2.GaussianBlur(source_highlight, (5, 5), 0)[:, :, np.newaxis]
    overlay_alpha = overlay_alpha * (1 - source_highlight * 0.7)
    
    # 混合
    blended = overlay_alpha * overlay_bgr + (1 - overlay_alpha) * base_roi
    img_target[py1:py2, px1:px2] = np.clip(blended, 0, 255).astype(np.uint8)
    
    cv2.imwrite(f'{OUTPUT_DIR}/result_final.jpg', img_target)
    print(f"  已保存: {OUTPUT_DIR}/result_final.jpg")
    
    # 生成细节图
    detail = img_target[550:700, 580:760]
    detail = cv2.resize(detail, (360, 300), interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(f'{OUTPUT_DIR}/detail_final.jpg', detail)
    print(f"  已保存: {OUTPUT_DIR}/detail_final.jpg")
    
    return img_target


def step4_preview(result):
    """步骤4：预览结果"""
    print("\n" + "=" * 50)
    print("  步骤4：预览结果")
    print("=" * 50)
    print("\n操作说明：")
    print("  空格键/回车：保存并退出")
    print("  R 键：重新开始")
    print("  Q 键：不保存退出")
    
    # 显示结果
    h, w = result.shape[:2]
    display = cv2.resize(result, (w // 2, h // 2))
    
    window = 'Step4: Yulan Jieguo (SPACE=Baocun, R=Chongxin, Q=Tuichu)'
    cv2.namedWindow(window)
    
    while True:
        cv2.imshow(window, display)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' ') or key == 13:  # 空格或回车
            cv2.destroyAllWindows()
            return 'save'
        elif key == ord('r') or key == ord('R'):
            cv2.destroyAllWindows()
            return 'restart'
        elif key == ord('q') or key == ord('Q'):
            cv2.destroyAllWindows()
            return 'quit'


def main():
    print("\n" + "=" * 50)
    print("  美瞳替换工具 - 交互式版本")
    print("=" * 50)
    print("\n这个工具将引导你完成以下步骤：")
    print("  1. 定位源图片中的美瞳区域")
    print("  2. 定位目标图片中的眼球区域")
    print("  3. 提取纹理并应用")
    print("  4. 预览和保存结果")
    
    while True:
        # 步骤1
        if not step1_locate_source():
            print("\n已退出。")
            break
        
        # 步骤2
        if not step2_locate_target():
            print("\n已退出。")
            break
        
        # 步骤3
        result = step3_extract_and_apply()
        
        # 步骤4
        action = step4_preview(result)
        
        if action == 'save':
            print("\n" + "=" * 50)
            print("  完成！")
            print("=" * 50)
            print(f"\n最终结果已保存到: {OUTPUT_DIR}/result_final.jpg")
            print(f"细节图已保存到: {OUTPUT_DIR}/detail_final.jpg")
            break
        elif action == 'restart':
            print("\n重新开始...")
            continue
        else:
            print("\n已退出，未保存。")
            break


if __name__ == "__main__":
    main()
