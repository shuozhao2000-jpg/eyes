"""
美瞳替换软件 - 图形界面版
"""
import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

class LensApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("美瞳替换软件 v1.0")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # 数据
        self.source_path = None
        self.target_path = None
        self.source_img = None
        self.target_img = None
        
        # 定位参数
        self.source_cx, self.source_cy = 0, 0
        self.source_top = self.source_bottom = self.source_left = self.source_right = 100
        self.target_cx, self.target_cy = 0, 0
        self.target_top = self.target_bottom = self.target_left = self.target_right = 30
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        title = tk.Label(self.root, text="美瞳替换软件", 
                        font=("Microsoft YaHei", 24, "bold"),
                        fg='#ffffff', bg='#2b2b2b')
        title.pack(pady=20)
        
        # 主框架
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill='both', expand=True, padx=40, pady=10)
        
        # 左侧 - 眼部图
        left_frame = tk.LabelFrame(main_frame, text="① 眼部图（美瞳素材）", 
                                   font=("Microsoft YaHei", 12),
                                   fg='#ffffff', bg='#3c3c3c', padx=10, pady=10)
        left_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        self.source_label = tk.Label(left_frame, text="未选择", 
                                     font=("Microsoft YaHei", 10),
                                     fg='#888888', bg='#3c3c3c',
                                     width=25, height=8)
        self.source_label.pack(pady=10)
        
        btn_source = tk.Button(left_frame, text="选择眼部图", 
                               font=("Microsoft YaHei", 11),
                               command=self.select_source,
                               bg='#4a90d9', fg='white',
                               width=15, height=2)
        btn_source.pack(pady=10)
        
        # 右侧 - 模特图
        right_frame = tk.LabelFrame(main_frame, text="② 模特图", 
                                    font=("Microsoft YaHei", 12),
                                    fg='#ffffff', bg='#3c3c3c', padx=10, pady=10)
        right_frame.pack(side='right', fill='both', expand=True, padx=10)
        
        self.target_label = tk.Label(right_frame, text="未选择", 
                                     font=("Microsoft YaHei", 10),
                                     fg='#888888', bg='#3c3c3c',
                                     width=25, height=8)
        self.target_label.pack(pady=10)
        
        btn_target = tk.Button(right_frame, text="选择模特图", 
                               font=("Microsoft YaHei", 11),
                               command=self.select_target,
                               bg='#4a90d9', fg='white',
                               width=15, height=2)
        btn_target.pack(pady=10)
        
        # 开始按钮
        btn_frame = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame.pack(pady=30)
        
        self.btn_start = tk.Button(btn_frame, text="开始替换", 
                                   font=("Microsoft YaHei", 14, "bold"),
                                   command=self.start_process,
                                   bg='#5cb85c', fg='white',
                                   width=20, height=2,
                                   state='disabled')
        self.btn_start.pack()
        
        # 状态栏
        self.status = tk.Label(self.root, text="请先选择眼部图和模特图", 
                               font=("Microsoft YaHei", 10),
                               fg='#888888', bg='#2b2b2b')
        self.status.pack(side='bottom', pady=10)
    
    def read_image(self, path):
        """读取图片（支持中文路径）"""
        # 使用numpy读取，支持中文路径
        img_array = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img
    
    def select_source(self):
        """选择眼部图"""
        path = filedialog.askopenfilename(
            title="选择眼部图（美瞳素材）",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.bmp")]
        )
        if path:
            self.source_path = path
            self.source_img = self.read_image(path)
            if self.source_img is None:
                messagebox.showerror("错误", "无法读取图片文件")
                return
            filename = os.path.basename(path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            self.source_label.config(text=f"✓ {filename}", fg='#5cb85c')
            self.check_ready()
    
    def select_target(self):
        """选择模特图"""
        path = filedialog.askopenfilename(
            title="选择模特图",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.bmp")]
        )
        if path:
            self.target_path = path
            self.target_img = self.read_image(path)
            if self.target_img is None:
                messagebox.showerror("错误", "无法读取图片文件")
                return
            filename = os.path.basename(path)
            if len(filename) > 20:
                filename = filename[:17] + "..."
            self.target_label.config(text=f"✓ {filename}", fg='#5cb85c')
            self.check_ready()
    
    def check_ready(self):
        """检查是否可以开始"""
        if self.source_path and self.target_path:
            self.btn_start.config(state='normal')
            self.status.config(text="点击「开始替换」进行下一步")
        else:
            self.btn_start.config(state='disabled')
    
    def start_process(self):
        """开始处理流程"""
        self.root.withdraw()  # 隐藏主窗口
        
        # 步骤1：定位眼部图
        self.status.config(text="正在定位眼部图...")
        if not self.locate_source():
            self.root.deiconify()
            return
        
        # 步骤2：定位模特图
        self.status.config(text="正在定位模特图...")
        if not self.locate_target():
            self.root.deiconify()
            return
        
        # 步骤3：生成结果
        self.status.config(text="正在生成结果...")
        result = self.process()
        
        if result is not None:
            # 保存结果
            output_path = 'output/result.jpg'
            cv2.imwrite(output_path, result)
            
            # 显示结果
            self.show_result(result, output_path)
        
        self.root.deiconify()
    
    def locate_source(self):
        """定位眼部图"""
        img = self.source_img.copy()
        h, w = img.shape[:2]
        self.source_cx, self.source_cy = w // 2, h // 2
        
        # 窗口缩放比例（可调）
        view_scale = [min(800 / w, 600 / h, 1.0)]
        
        def mouse_cb(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.source_cx = int(x / view_scale[0])
                self.source_cy = int(y / view_scale[0])
            elif event == cv2.EVENT_MOUSEWHEEL:
                d = 5 if flags > 0 else -5
                self.source_top = max(10, self.source_top + d)
                self.source_bottom = max(10, self.source_bottom + d)
                self.source_left = max(10, self.source_left + d)
                self.source_right = max(10, self.source_right + d)
        
        def draw():
            disp = img.copy()
            pts = []
            for i in range(72):
                a = 2 * np.pi * i / 72
                c, s = np.cos(a), np.sin(a)
                ry = self.source_top if s < 0 else self.source_bottom
                rx = self.source_left if c < 0 else self.source_right
                pts.append([int(self.source_cx + rx * c), int(self.source_cy + ry * s)])
            cv2.polylines(disp, [np.array(pts)], True, (0, 255, 0), 2)
            cv2.circle(disp, (self.source_cx, self.source_cy), 3, (0, 0, 255), -1)
            disp = cv2.resize(disp, (int(w * view_scale[0]), int(h * view_scale[0])))
            cv2.putText(disp, "[W/S]Shang [I/K]Xia [A/D]Zuo [J/L]You [Z/X]Zoom", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(disp, "[SPACE]OK [ESC]Cancel [R]Reset", 
                       (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(disp, f"T:{self.source_top} B:{self.source_bottom} L:{self.source_left} R:{self.source_right} Zoom:{int(view_scale[0]*100)}%", 
                       (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            return disp
        
        win = 'Step1: Locate Lens'
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(win, mouse_cb)
        
        while True:
            cv2.imshow(win, draw())
            k = cv2.waitKey(30)  # 增加等待时间
            
            if k == -1:
                continue
            
            k = k & 0xFF
            
            if k == 32:  # SPACE
                cv2.destroyAllWindows()
                return True
            elif k == 27:  # ESC
                cv2.destroyAllWindows()
                return False
            elif k == ord('q') or k == ord('Q'):
                cv2.destroyAllWindows()
                return False
            elif k == ord('w') or k == ord('W'):
                self.source_top += 5
            elif k == ord('s') or k == ord('S'):
                self.source_top = max(10, self.source_top - 5)
            elif k == ord('i') or k == ord('I'):
                self.source_bottom += 5
            elif k == ord('k') or k == ord('K'):
                self.source_bottom = max(10, self.source_bottom - 5)
            elif k == ord('a') or k == ord('A'):
                self.source_left += 5
            elif k == ord('d') or k == ord('D'):
                self.source_left = max(10, self.source_left - 5)
            elif k == ord('j') or k == ord('J'):
                self.source_right = max(10, self.source_right - 5)
            elif k == ord('l') or k == ord('L'):
                self.source_right += 5
            elif k == ord('r') or k == ord('R'):
                avg = (self.source_top + self.source_bottom + self.source_left + self.source_right) // 4
                self.source_top = self.source_bottom = self.source_left = self.source_right = avg
            elif k == ord('z') or k == ord('Z'):
                view_scale[0] = min(3.0, view_scale[0] + 0.2)  # 放大
            elif k == ord('x') or k == ord('X'):
                view_scale[0] = max(0.2, view_scale[0] - 0.2)  # 缩小
    
    def locate_target(self):
        """定位模特图（四边可调）"""
        img = self.target_img.copy()
        h, w = img.shape[:2]
        self.target_cx, self.target_cy = w // 2, h // 2
        
        # 窗口缩放比例（可调）
        view_scale = [min(900 / w, 700 / h, 1.0)]
        
        def mouse_cb(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.target_cx = int(x / view_scale[0])
                self.target_cy = int(y / view_scale[0])
            elif event == cv2.EVENT_MOUSEWHEEL:
                d = 5 if flags > 0 else -5
                self.target_top = max(10, self.target_top + d)
                self.target_bottom = max(10, self.target_bottom + d)
                self.target_left = max(10, self.target_left + d)
                self.target_right = max(10, self.target_right + d)
        
        def draw():
            disp = img.copy()
            # 画四边可调的形状
            pts = []
            for i in range(72):
                a = 2 * np.pi * i / 72
                c, s = np.cos(a), np.sin(a)
                ry = self.target_top if s < 0 else self.target_bottom
                rx = self.target_left if c < 0 else self.target_right
                pts.append([int(self.target_cx + rx * c), int(self.target_cy + ry * s)])
            cv2.polylines(disp, [np.array(pts)], True, (0, 255, 0), 2)
            cv2.circle(disp, (self.target_cx, self.target_cy), 3, (0, 0, 255), -1)
            disp = cv2.resize(disp, (int(w * view_scale[0]), int(h * view_scale[0])))
            cv2.putText(disp, "[W/S]Shang [I/K]Xia [A/D]Zuo [J/L]You [Z/X]Zoom", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(disp, "[SPACE]OK [ESC]Cancel [R]Reset", 
                       (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(disp, f"T:{self.target_top} B:{self.target_bottom} L:{self.target_left} R:{self.target_right} Zoom:{int(view_scale[0]*100)}%", 
                       (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            return disp
        
        win = 'Step2: Locate Eye'
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(win, mouse_cb)
        
        while True:
            cv2.imshow(win, draw())
            k = cv2.waitKey(30)
            
            if k == -1:
                continue
                
            k = k & 0xFF
            
            if k == 32:  # SPACE
                cv2.destroyAllWindows()
                return True
            elif k == 27 or k == ord('q') or k == ord('Q'):  # ESC or Q
                cv2.destroyAllWindows()
                return False
            # 四边控制（和眼部图一样）
            elif k == ord('w') or k == ord('W'):
                self.target_top += 5
            elif k == ord('s') or k == ord('S'):
                self.target_top = max(10, self.target_top - 5)
            elif k == ord('i') or k == ord('I'):
                self.target_bottom += 5
            elif k == ord('k') or k == ord('K'):
                self.target_bottom = max(10, self.target_bottom - 5)
            elif k == ord('a') or k == ord('A'):
                self.target_left += 5
            elif k == ord('d') or k == ord('D'):
                self.target_left = max(10, self.target_left - 5)
            elif k == ord('j') or k == ord('J'):
                self.target_right = max(10, self.target_right - 5)
            elif k == ord('l') or k == ord('L'):
                self.target_right += 5
            elif k == ord('r') or k == ord('R'):
                avg = (self.target_top + self.target_bottom + self.target_left + self.target_right) // 4
                self.target_top = self.target_bottom = self.target_left = self.target_right = avg
            elif k == ord('z') or k == ord('Z'):
                view_scale[0] = min(3.0, view_scale[0] + 0.2)  # 放大
            elif k == ord('x') or k == ord('X'):
                view_scale[0] = max(0.2, view_scale[0] - 0.2)  # 缩小
    
    def process(self):
        """处理并生成结果"""
        # 提取纹理
        max_r = max(self.source_top, self.source_bottom, self.source_left, self.source_right)
        sh, sw = self.source_img.shape[:2]
        
        x1, y1 = max(0, self.source_cx - max_r), max(0, self.source_cy - max_r)
        x2, y2 = min(sw, self.source_cx + max_r), min(sh, self.source_cy + max_r)
        
        cropped = self.source_img[y1:y2, x1:x2].copy()
        ch, cw = cropped.shape[:2]
        cx, cy = self.source_cx - x1, self.source_cy - y1
        
        alpha = np.zeros((ch, cw), dtype=np.float32)
        feather = 30
        for y in range(ch):
            for x in range(cw):
                dx, dy = x - cx, y - cy
                ry = self.source_top if dy < 0 else self.source_bottom
                rx = self.source_left if dx < 0 else self.source_right
                if rx > 0 and ry > 0:
                    dist = np.sqrt((dx/rx)**2 + (dy/ry)**2)
                    if dist <= 1:
                        if dist > 1 - feather/max(rx,ry):
                            alpha[y,x] = (1-dist)/(feather/max(rx,ry))
                        else:
                            alpha[y,x] = 1.0
        
        texture = np.dstack([cropped, (alpha*255).astype(np.uint8)])
        
        # 应用到目标
        result = self.target_img.copy()
        th, tw = texture.shape[:2]
        
        # 计算缩放（使用目标区域的平均半径）
        target_avg_radius = (self.target_top + self.target_bottom + self.target_left + self.target_right) // 4
        scale = (target_avg_radius / (min(th,tw)//2)) * 1.1
        
        nw, nh = int(tw*scale), int(th*scale)
        if nw < 1 or nh < 1: return None
        
        scaled = cv2.resize(texture, (nw, nh))
        
        px1 = self.target_cx - nw//2
        py1 = self.target_cy - nh//2
        px2, py2 = px1 + nw, py1 + nh
        
        ox1, oy1, ox2, oy2 = 0, 0, nw, nh
        bh, bw = result.shape[:2]
        
        if px1 < 0: ox1, px1 = -px1, 0
        if py1 < 0: oy1, py1 = -py1, 0
        if px2 > bw: ox2, px2 = ox2-(px2-bw), bw
        if py2 > bh: oy2, py2 = oy2-(py2-bh), bh
        
        if px1 >= px2 or py1 >= py2: return None
        
        roi = scaled[oy1:oy2, ox1:ox2]
        base = result[py1:py2, px1:px2].astype(float)
        original = base.copy()
        
        bgr = roi[:,:,:3].astype(float)
        a = roi[:,:,3:4].astype(float) / 255.0
        
        # 排除高光区域（眼睛反光）
        gray = cv2.cvtColor(roi[:,:,:3], cv2.COLOR_BGR2GRAY)
        highlight_mask = (gray > 210).astype(float)
        highlight_mask = cv2.GaussianBlur(highlight_mask, (9,9), 0)[:,:,np.newaxis]
        
        # 完全覆盖模式：直接用纹理颜色替换，不做任何混合
        # 有纹理的地方（alpha > 0）直接用纹理颜色
        full_replace = a * (1 - highlight_mask)
        
        # 直接替换，不混合底色
        blended = bgr * full_replace + original * (1 - full_replace)
        
        result[py1:py2, px1:px2] = np.clip(blended, 0, 255).astype(np.uint8)
        
        return result
    
    def show_result(self, result, path):
        """显示结果"""
        win = tk.Toplevel(self.root)
        win.title("结果预览")
        win.configure(bg='#2b2b2b')
        
        # 转换图片
        rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        scale = min(800/w, 600/h, 1.0)
        rgb = cv2.resize(rgb, (int(w*scale), int(h*scale)))
        
        img = Image.fromarray(rgb)
        photo = ImageTk.PhotoImage(img)
        
        label = tk.Label(win, image=photo)
        label.image = photo
        label.pack(padx=10, pady=10)
        
        tk.Label(win, text=f"已保存到: {path}", 
                font=("Microsoft YaHei", 10),
                fg='#5cb85c', bg='#2b2b2b').pack(pady=5)
        
        btn_frame = tk.Frame(win, bg='#2b2b2b')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="打开文件", 
                 command=lambda: os.startfile(os.path.abspath(path)),
                 bg='#4a90d9', fg='white').pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="关闭", 
                 command=win.destroy,
                 bg='#888888', fg='white').pack(side='left', padx=5)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if not os.path.exists('output'):
        os.makedirs('output')
    app = LensApp()
    app.run()
