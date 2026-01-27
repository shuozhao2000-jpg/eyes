"""
美瞳替换软件 v1.0

功能：
- 上传任意眼部图（美瞳素材）
- 上传任意模特图
- 交互式定位
- 生成结果

使用方法：
python lens_replacer.py
"""
import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import sys

class LensReplacer:
    def __init__(self):
        # 图片路径
        self.source_path = None  # 眼部图（美瞳素材）
        self.target_path = None  # 模特图
        
        # 源图片定位参数
        self.source_cx, self.source_cy = 0, 0
        self.source_top = 100
        self.source_bottom = 100
        self.source_left = 100
        self.source_right = 100
        self.source_feather = 30
        
        # 目标图片定位参数
        self.target_cx, self.target_cy = 0, 0
        self.target_radius = 30
        
        # 图片数据
        self.source_img = None
        self.target_img = None
        
        # 输出目录
        self.output_dir = 'output'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def select_source_image(self):
        """选择眼部图（美瞳素材）"""
        root = tk.Tk()
        root.withdraw()
        
        file_path = filedialog.askopenfilename(
            title="选择眼部图（美瞳素材）",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        root.destroy()
        
        if file_path:
            self.source_path = file_path
            self.source_img = cv2.imread(file_path)
            if self.source_img is not None:
                h, w = self.source_img.shape[:2]
                self.source_cx = w // 2
                self.source_cy = h // 2
                print(f"已加载眼部图: {file_path}")
                print(f"  尺寸: {w} x {h}")
                return True
            else:
                print(f"错误：无法加载图片 {file_path}")
                return False
        return False
    
    def select_target_image(self):
        """选择模特图"""
        root = tk.Tk()
        root.withdraw()
        
        file_path = filedialog.askopenfilename(
            title="选择模特图",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp"),
                ("所有文件", "*.*")
            ]
        )
        root.destroy()
        
        if file_path:
            self.target_path = file_path
            self.target_img = cv2.imread(file_path)
            if self.target_img is not None:
                h, w = self.target_img.shape[:2]
                self.target_cx = w // 2
                self.target_cy = h // 2
                print(f"已加载模特图: {file_path}")
                print(f"  尺寸: {w} x {h}")
                return True
            else:
                print(f"错误：无法加载图片 {file_path}")
                return False
        return False
    
    def locate_source(self):
        """交互式定位源图片中的美瞳区域"""
        if self.source_img is None:
            print("错误：请先加载眼部图")
            return False
        
        print("\n" + "=" * 50)
        print("  步骤1：定位眼部图中的美瞳区域")
        print("=" * 50)
        print("\n操作说明：")
        print("  鼠标左键点击：设置圆心位置")
        print("  滚轮：调整整体大小")
        print("  W/S：上边 往上/往下")
        print("  I/K：下边 往下/往上")
        print("  A/D：左边 往左/往右")
        print("  J/L：右边 往左/往右")
        print("  R：重置为圆形")
        print("  空格：确认并继续")
        print("  Q：退出")
        
        img = self.source_img.copy()
        h, w = img.shape[:2]
        
        # 计算缩放比例，使窗口大小适中
        max_display = 800
        scale = min(max_display / w, max_display / h, 1.0)
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.source_cx = int(x / scale)
                self.source_cy = int(y / scale)
            elif event == cv2.EVENT_MOUSEWHEEL:
                delta = 5 if flags > 0 else -5
                self.source_top = max(10, self.source_top + delta)
                self.source_bottom = max(10, self.source_bottom + delta)
                self.source_left = max(10, self.source_left + delta)
                self.source_right = max(10, self.source_right + delta)
        
        def update_display():
            display = img.copy()
            
            # 画四边可调的形状
            points = []
            for i in range(72):
                angle = 2 * np.pi * i / 72
                cos_a, sin_a = np.cos(angle), np.sin(angle)
                ry = self.source_top if sin_a < 0 else self.source_bottom
                rx = self.source_left if cos_a < 0 else self.source_right
                points.append([int(self.source_cx + rx * cos_a), 
                              int(self.source_cy + ry * sin_a)])
            cv2.polylines(display, [np.array(points, dtype=np.int32)], True, (0, 255, 0), 2)
            cv2.circle(display, (self.source_cx, self.source_cy), 3, (0, 0, 255), -1)
            
            # 画四条边的标记
            cv2.line(display, (self.source_cx, self.source_cy - self.source_top), 
                     (self.source_cx, self.source_cy - self.source_top - 15), (0, 255, 255), 2)
            cv2.line(display, (self.source_cx, self.source_cy + self.source_bottom), 
                     (self.source_cx, self.source_cy + self.source_bottom + 15), (255, 0, 255), 2)
            cv2.line(display, (self.source_cx - self.source_left, self.source_cy), 
                     (self.source_cx - self.source_left - 15, self.source_cy), (255, 255, 0), 2)
            cv2.line(display, (self.source_cx + self.source_right, self.source_cy), 
                     (self.source_cx + self.source_right + 15, self.source_cy), (0, 165, 255), 2)
            
            # 缩放显示
            display = cv2.resize(display, (int(w * scale), int(h * scale)))
            
            # 添加说明
            cv2.putText(display, f"Center: ({self.source_cx}, {self.source_cy})", (10, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(display, f"T:{self.source_top} B:{self.source_bottom} L:{self.source_left} R:{self.source_right}", 
                        (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display, "[W/S]Shang [I/K]Xia [A/D]Zuo [J/L]You [R]Reset", (10, 75), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
            cv2.putText(display, "[SPACE]Queren [Q]Tuichu", (10, 95), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
            return display
        
        window = 'Dingwei Meitong (SPACE=Queren, Q=Tuichu)'
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
                self.source_top += 3
            elif key == ord('s') or key == ord('S'):
                self.source_top = max(10, self.source_top - 3)
            elif key == ord('i') or key == ord('I'):
                self.source_bottom += 3
            elif key == ord('k') or key == ord('K'):
                self.source_bottom = max(10, self.source_bottom - 3)
            elif key == ord('a') or key == ord('A'):
                self.source_left += 3
            elif key == ord('d') or key == ord('D'):
                self.source_left = max(10, self.source_left - 3)
            elif key == ord('j') or key == ord('J'):
                self.source_right = max(10, self.source_right - 3)
            elif key == ord('l') or key == ord('L'):
                self.source_right += 3
            elif key == ord('r') or key == ord('R'):
                avg = (self.source_top + self.source_bottom + self.source_left + self.source_right) // 4
                self.source_top = self.source_bottom = self.source_left = self.source_right = avg
    
    def locate_target(self):
        """交互式定位目标图片中的眼球区域"""
        if self.target_img is None:
            print("错误：请先加载模特图")
            return False
        
        print("\n" + "=" * 50)
        print("  步骤2：定位模特图中的眼球区域")
        print("=" * 50)
        print("\n操作说明：")
        print("  鼠标左键点击：设置圆心位置")
        print("  滚轮：调整半径大小")
        print("  空格：确认并继续")
        print("  Q：退出")
        
        img = self.target_img.copy()
        h, w = img.shape[:2]
        
        # 计算缩放比例
        max_display = 900
        scale = min(max_display / w, max_display / h, 1.0)
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.target_cx = int(x / scale)
                self.target_cy = int(y / scale)
            elif event == cv2.EVENT_MOUSEWHEEL:
                self.target_radius = max(5, self.target_radius + (3 if flags > 0 else -3))
        
        def update_display():
            display = img.copy()
            cv2.circle(display, (self.target_cx, self.target_cy), self.target_radius, (0, 255, 0), 2)
            cv2.circle(display, (self.target_cx, self.target_cy), 3, (0, 0, 255), -1)
            
            # 缩放显示
            display = cv2.resize(display, (int(w * scale), int(h * scale)))
            
            cv2.putText(display, f"Center: ({self.target_cx}, {self.target_cy})  Radius: {self.target_radius}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display, "[Click]Zhongxin [Scroll]Banjing [SPACE]Queren [Q]Tuichu", 
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            return display
        
        window = 'Dingwei Yanqiu (SPACE=Queren, Q=Tuichu)'
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
    
    def extract_and_apply(self):
        """提取纹理并应用到目标"""
        print("\n" + "=" * 50)
        print("  步骤3：提取纹理并应用")
        print("=" * 50)
        
        # 提取纹理
        print("\n正在提取美瞳纹理...")
        
        max_r = max(self.source_top, self.source_bottom, self.source_left, self.source_right)
        sh, sw = self.source_img.shape[:2]
        
        x1 = max(0, self.source_cx - max_r)
        y1 = max(0, self.source_cy - max_r)
        x2 = min(sw, self.source_cx + max_r)
        y2 = min(sh, self.source_cy + max_r)
        
        cropped = self.source_img[y1:y2, x1:x2].copy()
        ch, cw = cropped.shape[:2]
        center_x = self.source_cx - x1
        center_y = self.source_cy - y1
        
        # 创建Alpha蒙版
        alpha = np.zeros((ch, cw), dtype=np.float32)
        for y in range(ch):
            for x in range(cw):
                dx, dy = x - center_x, y - center_y
                ry = self.source_top if dy < 0 else self.source_bottom
                rx = self.source_left if dx < 0 else self.source_right
                if rx > 0 and ry > 0:
                    dist = np.sqrt((dx / rx)**2 + (dy / ry)**2)
                    if dist <= 1:
                        if dist > 1 - self.source_feather / max(rx, ry):
                            alpha[y, x] = (1 - dist) / (self.source_feather / max(rx, ry))
                        else:
                            alpha[y, x] = 1.0
        
        alpha = (alpha * 255).astype(np.uint8)
        texture = np.dstack([cropped, alpha])
        
        cv2.imwrite(f'{self.output_dir}/extracted_texture.png', texture)
        print(f"  已保存纹理: {self.output_dir}/extracted_texture.png")
        
        # 应用到目标
        print("\n正在应用纹理...")
        result = self.target_img.copy()
        
        # 计算缩放
        th, tw = texture.shape[:2]
        texture_radius = min(th, tw) // 2
        scale = (self.target_radius / texture_radius) * 1.1
        
        new_w, new_h = int(tw * scale), int(th * scale)
        if new_w < 1 or new_h < 1:
            print("错误：缩放比例太小")
            return None
            
        scaled = cv2.resize(texture, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # 计算叠加位置
        px1 = self.target_cx - new_w // 2
        py1 = self.target_cy - new_h // 2
        px2, py2 = px1 + new_w, py1 + new_h
        
        ox1, oy1, ox2, oy2 = 0, 0, new_w, new_h
        bh, bw = result.shape[:2]
        
        if px1 < 0: ox1, px1 = -px1, 0
        if py1 < 0: oy1, py1 = -py1, 0
        if px2 > bw: ox2, px2 = ox2 - (px2 - bw), bw
        if py2 > bh: oy2, py2 = oy2 - (py2 - bh), bh
        
        if px1 >= px2 or py1 >= py2:
            print("错误：叠加区域无效")
            return None
        
        overlay_roi = scaled[oy1:oy2, ox1:ox2]
        base_roi = result[py1:py2, px1:px2].astype(float)
        
        overlay_bgr = overlay_roi[:, :, :3].astype(float)
        overlay_alpha = overlay_roi[:, :, 3:4].astype(float) / 255.0
        
        # 排除源纹理高光
        overlay_gray = cv2.cvtColor(overlay_roi[:, :, :3], cv2.COLOR_BGR2GRAY)
        source_highlight = (overlay_gray > 220).astype(float)
        source_highlight = cv2.GaussianBlur(source_highlight, (5, 5), 0)[:, :, np.newaxis]
        overlay_alpha = overlay_alpha * (1 - source_highlight * 0.7)
        
        # 混合
        blended = overlay_alpha * overlay_bgr + (1 - overlay_alpha) * base_roi
        result[py1:py2, px1:px2] = np.clip(blended, 0, 255).astype(np.uint8)
        
        # 保存结果
        output_path = f'{self.output_dir}/result.jpg'
        cv2.imwrite(output_path, result)
        print(f"  已保存结果: {output_path}")
        
        return result
    
    def preview_result(self, result):
        """预览结果"""
        if result is None:
            return 'quit'
        
        print("\n" + "=" * 50)
        print("  步骤4：预览结果")
        print("=" * 50)
        print("\n操作说明：")
        print("  空格/回车：保存并退出")
        print("  R：重新开始")
        print("  Q：不保存退出")
        
        h, w = result.shape[:2]
        max_display = 900
        scale = min(max_display / w, max_display / h, 1.0)
        display = cv2.resize(result, (int(w * scale), int(h * scale)))
        
        window = 'Yulan Jieguo (SPACE=Baocun, R=Chongxin, Q=Tuichu)'
        cv2.namedWindow(window)
        
        while True:
            cv2.imshow(window, display)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' ') or key == 13:
                cv2.destroyAllWindows()
                return 'save'
            elif key == ord('r') or key == ord('R'):
                cv2.destroyAllWindows()
                return 'restart'
            elif key == ord('q') or key == ord('Q'):
                cv2.destroyAllWindows()
                return 'quit'
    
    def run(self):
        """运行主程序"""
        print("\n" + "=" * 50)
        print("  美瞳替换软件 v1.0")
        print("=" * 50)
        print("\n欢迎使用美瞳替换软件！")
        print("\n这个软件将引导你完成以下步骤：")
        print("  1. 选择眼部图（美瞳素材）")
        print("  2. 选择模特图")
        print("  3. 定位美瞳区域")
        print("  4. 定位目标眼球")
        print("  5. 生成并预览结果")
        
        while True:
            # 选择图片
            print("\n" + "-" * 30)
            print("请选择眼部图（美瞳素材）...")
            if not self.select_source_image():
                print("未选择眼部图，退出。")
                break
            
            print("\n请选择模特图...")
            if not self.select_target_image():
                print("未选择模特图，退出。")
                break
            
            # 定位
            if not self.locate_source():
                print("已取消定位，退出。")
                break
            
            if not self.locate_target():
                print("已取消定位，退出。")
                break
            
            # 生成
            result = self.extract_and_apply()
            
            # 预览
            action = self.preview_result(result)
            
            if action == 'save':
                print("\n" + "=" * 50)
                print("  完成！")
                print("=" * 50)
                print(f"\n结果已保存到: {self.output_dir}/result.jpg")
                
                # 询问是否继续
                print("\n按任意键继续处理下一张，或关闭窗口退出...")
                root = tk.Tk()
                root.withdraw()
                if messagebox.askyesno("完成", "是否继续处理下一张图片？"):
                    root.destroy()
                    continue
                root.destroy()
                break
            elif action == 'restart':
                print("\n重新开始...")
                continue
            else:
                print("\n已退出。")
                break
        
        print("\n感谢使用！")


def main():
    app = LensReplacer()
    app.run()


if __name__ == "__main__":
    main()
