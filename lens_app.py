"""
美瞳替换软件 - 图形界面版
"""
import cv2
import numpy as np
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime

class LensApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("美瞳替换软件 v1.0")
        self.root.geometry("900x650")
        self.root.configure(bg='#2b2b2b')
        
        # 数据
        self.source_path = None
        self.target_path = None
        self.source_img = None
        self.target_img = None
        
        # 定位参数 - 画笔圈出的点
        self.source_points = []  # 眼部图圈出的区域
        self.target_points = []  # 模特图圈出的区域（可多个眼睛）
        self.current_target_points = []  # 当前正在画的区域
        
        # 历史记录文件
        self.history_file = 'output/lens_history.json'
        self.target_history_file = 'output/target_history.json'
        self.lens_history = self.load_history(self.history_file)
        self.target_history = self.load_history(self.target_history_file)
        self.selected_history = None  # 选中的眼部图历史记录
        self.selected_target_history = None  # 选中的模特图历史记录
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        # 标题
        title = tk.Label(self.root, text="美瞳替换软件", 
                        font=("Microsoft YaHei", 20, "bold"),
                        fg='#ffffff', bg='#2b2b2b')
        title.pack(pady=10)
        
        # ====== 第一行：眼部图 ======
        row1 = tk.Frame(self.root, bg='#2b2b2b')
        row1.pack(fill='both', expand=True, padx=15, pady=5)
        
        # 左侧 - 选择眼部图
        left1 = tk.LabelFrame(row1, text="① 选择眼部图（美瞳素材）", 
                              font=("Microsoft YaHei", 11),
                              fg='#ffffff', bg='#3c3c3c', padx=8, pady=8)
        left1.pack(side='left', fill='both', expand=True, padx=5)
        
        self.source_label = tk.Label(left1, text="未选择", 
                                     font=("Microsoft YaHei", 10),
                                     fg='#888888', bg='#3c3c3c',
                                     width=18, height=3)
        self.source_label.pack(pady=3)
        
        tk.Button(left1, text="选择新眼部图", 
                  font=("Microsoft YaHei", 10),
                  command=self.select_source,
                  bg='#4a90d9', fg='white',
                  width=14).pack(pady=3)
        
        # 右侧 - 眼部图历史记录
        right1 = tk.LabelFrame(row1, text="📋 眼部图历史（点击使用）", 
                               font=("Microsoft YaHei", 11),
                               fg='#ffffff', bg='#3c3c3c', padx=8, pady=8)
        right1.pack(side='right', fill='both', expand=True, padx=5)
        
        list1 = tk.Frame(right1, bg='#3c3c3c')
        list1.pack(fill='both', expand=True)
        
        self.history_listbox = tk.Listbox(list1, 
                                          font=("Microsoft YaHei", 9),
                                          bg='#2b2b2b', fg='#ffffff',
                                          selectbackground='#4a90d9',
                                          height=5, width=28)
        self.history_listbox.pack(side='left', fill='both', expand=True)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)
        
        sb1 = tk.Scrollbar(list1, command=self.history_listbox.yview)
        sb1.pack(side='right', fill='y')
        self.history_listbox.config(yscrollcommand=sb1.set)
        
        tk.Button(right1, text="删除", font=("Microsoft YaHei", 9),
                  command=self.delete_selected_history,
                  bg='#d9534f', fg='white', width=8).pack(pady=3)
        
        self.update_history_list()
        
        # ====== 第二行：模特图 ======
        row2 = tk.Frame(self.root, bg='#2b2b2b')
        row2.pack(fill='both', expand=True, padx=15, pady=5)
        
        # 左侧 - 选择模特图
        left2 = tk.LabelFrame(row2, text="② 选择模特图", 
                              font=("Microsoft YaHei", 11),
                              fg='#ffffff', bg='#3c3c3c', padx=8, pady=8)
        left2.pack(side='left', fill='both', expand=True, padx=5)
        
        self.target_label = tk.Label(left2, text="未选择", 
                                     font=("Microsoft YaHei", 10),
                                     fg='#888888', bg='#3c3c3c',
                                     width=18, height=3)
        self.target_label.pack(pady=3)
        
        tk.Button(left2, text="选择模特图", 
                  font=("Microsoft YaHei", 10),
                  command=self.select_target,
                  bg='#4a90d9', fg='white',
                  width=14).pack(pady=3)
        
        # 右侧 - 模特图历史记录
        right2 = tk.LabelFrame(row2, text="📋 模特图历史（点击使用）", 
                               font=("Microsoft YaHei", 11),
                               fg='#ffffff', bg='#3c3c3c', padx=8, pady=8)
        right2.pack(side='right', fill='both', expand=True, padx=5)
        
        list2 = tk.Frame(right2, bg='#3c3c3c')
        list2.pack(fill='both', expand=True)
        
        self.target_history_listbox = tk.Listbox(list2, 
                                                  font=("Microsoft YaHei", 9),
                                                  bg='#2b2b2b', fg='#ffffff',
                                                  selectbackground='#4a90d9',
                                                  height=5, width=28)
        self.target_history_listbox.pack(side='left', fill='both', expand=True)
        self.target_history_listbox.bind('<<ListboxSelect>>', self.on_target_history_select)
        
        sb2 = tk.Scrollbar(list2, command=self.target_history_listbox.yview)
        sb2.pack(side='right', fill='y')
        self.target_history_listbox.config(yscrollcommand=sb2.set)
        
        tk.Button(right2, text="删除", font=("Microsoft YaHei", 9),
                  command=self.delete_selected_target_history,
                  bg='#d9534f', fg='white', width=8).pack(pady=3)
        
        self.update_target_history_list()
        
        # ====== 开始按钮 ======
        btn_frame = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame.pack(pady=15)
        
        self.btn_start = tk.Button(btn_frame, text="开始替换", 
                                   font=("Microsoft YaHei", 14, "bold"),
                                   command=self.start_process,
                                   bg='#5cb85c', fg='white',
                                   width=20, height=2,
                                   state='disabled')
        self.btn_start.pack()
        
        # 状态栏
        self.status = tk.Label(self.root, text="请选择眼部图和模特图（或从历史记录选择）", 
                               font=("Microsoft YaHei", 10),
                               fg='#888888', bg='#2b2b2b')
        self.status.pack(side='bottom', pady=8)
    
    def load_history(self, filepath):
        """加载历史记录"""
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_history(self, history_list, filepath):
        """保存历史记录"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, ensure_ascii=False, indent=2)
    
    def add_to_history(self, name, points, img_path, is_target=False):
        """添加新记录"""
        record = {
            'name': name,
            'points': points,
            'img_path': img_path,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        if is_target:
            self.target_history.insert(0, record)
            if len(self.target_history) > 20:
                self.target_history = self.target_history[:20]
            self.save_history(self.target_history, self.target_history_file)
            self.update_target_history_list()
        else:
            self.lens_history.insert(0, record)
            if len(self.lens_history) > 20:
                self.lens_history = self.lens_history[:20]
            self.save_history(self.lens_history, self.history_file)
            self.update_history_list()
    
    def delete_history(self, index, is_target=False):
        """删除记录"""
        if is_target:
            if 0 <= index < len(self.target_history):
                del self.target_history[index]
                self.save_history(self.target_history, self.target_history_file)
                self.update_target_history_list()
        else:
            if 0 <= index < len(self.lens_history):
                del self.lens_history[index]
                self.save_history(self.lens_history, self.history_file)
                self.update_history_list()
    
    def update_history_list(self):
        """更新眼部图历史记录列表"""
        self.history_listbox.delete(0, tk.END)
        for i, record in enumerate(self.lens_history):
            display = f"{record['name']} ({record['time']})"
            self.history_listbox.insert(tk.END, display)
    
    def update_target_history_list(self):
        """更新模特图历史记录列表"""
        self.target_history_listbox.delete(0, tk.END)
        for i, record in enumerate(self.target_history):
            display = f"{record['name']} ({record['time']})"
            self.target_history_listbox.insert(tk.END, display)
    
    def on_history_select(self, event):
        """选中眼部图历史记录"""
        selection = self.history_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_history = self.lens_history[idx]
            self.source_points = [list(p) for p in self.selected_history['points']]
            name = self.selected_history['name']
            # 尝试加载对应的图片
            img_path = self.selected_history.get('img_path', '')
            if img_path and os.path.exists(img_path):
                self.source_img = self.read_image(img_path)
                self.source_path = img_path
            self.source_label.config(text=f"✓ {name}", fg='#5cb85c')
            self.status.config(text=f"已加载眼部图: {name}")
            self.check_ready()
    
    def on_target_history_select(self, event):
        """选中模特图历史记录"""
        selection = self.target_history_listbox.curselection()
        if selection:
            idx = selection[0]
            self.selected_target_history = self.target_history[idx]
            self.target_points = [[list(p) for p in region] for region in self.selected_target_history['points']]
            name = self.selected_target_history['name']
            # 尝试加载对应的图片
            img_path = self.selected_target_history.get('img_path', '')
            if img_path and os.path.exists(img_path):
                self.target_img = self.read_image(img_path)
                self.target_path = img_path
                self.target_label.config(text=f"✓ {name}", fg='#5cb85c')
            else:
                self.target_label.config(text=f"⚠ {name}(需选图)", fg='#f0ad4e')
            self.status.config(text=f"已加载模特图: {name}")
            self.check_ready()
    
    def delete_selected_history(self):
        """删除选中的眼部图历史记录"""
        selection = self.history_listbox.curselection()
        if selection:
            idx = selection[0]
            name = self.lens_history[idx]['name']
            if messagebox.askyesno("确认", f"确定删除「{name}」？"):
                self.delete_history(idx, is_target=False)
                self.selected_history = None
                self.source_points = []
    
    def delete_selected_target_history(self):
        """删除选中的模特图历史记录"""
        selection = self.target_history_listbox.curselection()
        if selection:
            idx = selection[0]
            name = self.target_history[idx]['name']
            if messagebox.askyesno("确认", f"确定删除「{name}」？"):
                self.delete_history(idx, is_target=True)
                self.selected_target_history = None
                self.target_points = []
    
    def ask_save_history(self):
        """询问是否保存到历史记录"""
        if messagebox.askyesno("保存记录", "是否将此美瞳圈选保存到历史记录？\n下次可直接使用，无需重新圈选"):
            # 使用简单对话框获取名称
            default_name = os.path.basename(self.source_path).rsplit('.', 1)[0] if self.source_path else "美瞳"
            from tkinter import simpledialog
            name = simpledialog.askstring("命名记录", "请输入名称：", initialvalue=default_name)
            if name and name.strip():
                self.add_to_history(name.strip(), self.source_points, self.source_path or "")
                messagebox.showinfo("成功", f"已保存「{name}」到历史记录")
    
    def ask_save_target_history(self):
        """询问是否保存模特图圈选到历史记录"""
        if messagebox.askyesno("保存记录", "是否将此模特图眼睛位置保存到历史记录？\n下次可直接使用，无需重新圈选"):
            default_name = os.path.basename(self.target_path).rsplit('.', 1)[0] if self.target_path else "模特"
            from tkinter import simpledialog
            name = simpledialog.askstring("命名记录", "请输入名称：", initialvalue=default_name)
            if name and name.strip():
                self.add_to_history(name.strip(), self.target_points, self.target_path or "", is_target=True)
                messagebox.showinfo("成功", f"已保存「{name}」到模特图历史记录")
    
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
        # 需要有眼部图或历史记录，并且有模特图或历史记录
        has_source = self.source_path or len(self.source_points) > 0
        has_target = self.target_path or len(self.target_points) > 0
        
        if has_source and has_target:
            self.btn_start.config(state='normal')
            self.status.config(text="点击「开始替换」进行下一步")
        else:
            self.btn_start.config(state='disabled')
    
    def start_process(self):
        """开始处理流程"""
        self.root.withdraw()  # 隐藏主窗口
        
        # 如果从模特图历史记录加载，需要加载对应的图片
        if self.selected_target_history and self.target_img is None:
            img_path = self.selected_target_history.get('img_path', '')
            if img_path and os.path.exists(img_path):
                self.target_img = self.read_image(img_path)
                self.target_path = img_path
        
        # 检查是否有必要的图片
        if self.source_img is None and self.source_path:
            self.source_img = self.read_image(self.source_path)
        if self.target_img is None and self.target_path:
            self.target_img = self.read_image(self.target_path)
        
        # 步骤1：定位眼部图（如果已有历史记录则跳过）
        if len(self.source_points) == 0:
            if self.source_img is None:
                messagebox.showerror("错误", "请先选择眼部图")
                self.root.deiconify()
                return
            self.status.config(text="正在定位眼部图...")
            if not self.locate_source():
                self.root.deiconify()
                return
        
        # 步骤2：定位模特图（如果已有历史记录则跳过）
        if len(self.target_points) == 0:
            if self.target_img is None:
                messagebox.showerror("错误", "请先选择模特图")
                self.root.deiconify()
                return
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
        """定位眼部图 - 用画笔圈出美瞳区域"""
        img = self.source_img.copy()
        h, w = img.shape[:2]
        self.source_points = []
        
        view_scale = [min(800 / w, 600 / h, 1.0)]
        offset_x, offset_y = [0], [0]
        drawing = [False]
        dragging = [False]
        moving = [False]  # 移动已画图形
        drag_start = [0, 0]
        move_start = [0, 0]
        current_points = []
        line_width = [3]
        circle_mode = [False]
        circle_center = [0, 0]
        circle_radius = [0]
        gap_angle = [60]  # 上方豁口角度（度）
        
        def mouse_cb(event, x, y, flags, param):
            ox = int((x - offset_x[0]) / view_scale[0])
            oy = int((y - offset_y[0]) / view_scale[0])
            
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing[0] = True
                if circle_mode[0]:
                    circle_center[0], circle_center[1] = ox, oy
                    circle_radius[0] = 0
                else:
                    current_points.clear()
                    current_points.append([ox, oy])
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing[0]:
                    if circle_mode[0]:
                        dx, dy = ox - circle_center[0], oy - circle_center[1]
                        circle_radius[0] = int(np.sqrt(dx*dx + dy*dy))
                    else:
                        current_points.append([ox, oy])
                elif dragging[0]:
                    offset_x[0] = x - drag_start[0]
                    offset_y[0] = y - drag_start[1]
                elif moving[0] and len(self.source_points) > 0:
                    # 移动已画的图形
                    dx = ox - move_start[0]
                    dy = oy - move_start[1]
                    self.source_points = [[p[0]+dx, p[1]+dy] for p in self.source_points]
                    move_start[0], move_start[1] = ox, oy
            elif event == cv2.EVENT_LBUTTONUP:
                drawing[0] = False
                if circle_mode[0] and circle_radius[0] > 5:
                    # 生成带豁口的弧形（上方留口）
                    pts = []
                    gap_half = gap_angle[0] / 2
                    start_deg = -90 + gap_half  # 从右上开始
                    end_deg = -90 - gap_half + 360  # 到左上结束
                    num_pts = 60
                    for i in range(num_pts + 1):
                        deg = start_deg + (end_deg - start_deg) * i / num_pts
                        a = np.radians(deg)
                        px = int(circle_center[0] + circle_radius[0] * np.cos(a))
                        py = int(circle_center[1] + circle_radius[0] * np.sin(a))
                        pts.append([px, py])
                    self.source_points = pts
                elif len(current_points) > 10:
                    self.source_points = current_points.copy()
            elif event == cv2.EVENT_RBUTTONDOWN:
                dragging[0] = True
                drag_start[0] = x - offset_x[0]
                drag_start[1] = y - offset_y[0]
            elif event == cv2.EVENT_RBUTTONUP:
                dragging[0] = False
            elif event == cv2.EVENT_MBUTTONDOWN:  # 中键移动图形
                moving[0] = True
                move_start[0], move_start[1] = ox, oy
            elif event == cv2.EVENT_MBUTTONUP:
                moving[0] = False
            elif event == cv2.EVENT_MOUSEWHEEL:  # 滚轮调整大小
                if len(self.source_points) > 0:
                    # 计算中心点
                    cx = sum(p[0] for p in self.source_points) // len(self.source_points)
                    cy = sum(p[1] for p in self.source_points) // len(self.source_points)
                    # 缩放比例
                    scale = 1.05 if flags > 0 else 0.95
                    # 缩放所有点
                    self.source_points = [[int(cx + (p[0]-cx)*scale), int(cy + (p[1]-cy)*scale)] 
                                          for p in self.source_points]
        
        def draw():
            disp = img.copy()
            lw = line_width[0]
            
            # 画圆形预览（带豁口）
            if circle_mode[0] and drawing[0] and circle_radius[0] > 0:
                gap_half = gap_angle[0] / 2
                start_a = int(-90 + gap_half)
                end_a = int(-90 - gap_half + 360)
                cv2.ellipse(disp, (circle_center[0], circle_center[1]), 
                           (circle_radius[0], circle_radius[0]), 0, start_a, end_a, (0, 255, 0), lw)
            elif len(current_points) > 1:
                pts = np.array(current_points, dtype=np.int32)
                cv2.polylines(disp, [pts], False, (0, 255, 0), lw)
            
            # 画已确定的区域（不闭合，留豁口）
            if len(self.source_points) > 1:
                pts = np.array(self.source_points, dtype=np.int32)
                cv2.polylines(disp, [pts], False, (0, 255, 0), lw)  # False=不闭合
            
            scaled = cv2.resize(disp, (int(w * view_scale[0]), int(h * view_scale[0])))
            
            canvas_h, canvas_w = 700, 900
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            canvas[:] = (40, 40, 40)
            
            sh, sw = scaled.shape[:2]
            px, py = int(offset_x[0]), int(offset_y[0])
            
            src_x1, src_y1 = max(0, -px), max(0, -py)
            src_x2, src_y2 = min(sw, canvas_w - px), min(sh, canvas_h - py)
            dst_x1, dst_y1 = max(0, px), max(0, py)
            dst_x2 = dst_x1 + (src_x2 - src_x1)
            dst_y2 = dst_y1 + (src_y2 - src_y1)
            
            if src_x2 > src_x1 and src_y2 > src_y1:
                canvas[dst_y1:dst_y2, dst_x1:dst_x2] = scaled[src_y1:src_y2, src_x1:src_x2]
            
            mode_str = "CIRCLE(gap)" if circle_mode[0] else "FREE"
            cv2.putText(canvas, f"Mode: {mode_str} | Middle: Move | Scroll: Resize", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
            cv2.putText(canvas, f"[O] Switch  [G] Gap:{gap_angle[0]}  [+/-] Line  [SPACE] OK", 
                       (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            return canvas
        
        win = 'Step1: Draw Lens Area'
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(win, mouse_cb)
        
        while True:
            cv2.imshow(win, draw())
            k = cv2.waitKey(30)
            
            if k == -1:
                continue
            k = k & 0xFF
            
            if k == 32:  # SPACE
                if len(self.source_points) > 10:
                    cv2.destroyAllWindows()
                    # 询问是否保存到历史记录
                    self.ask_save_history()
                    return True
            elif k == 27 or k == ord('q'):  # ESC
                cv2.destroyAllWindows()
                return False
            elif k == ord('c') or k == ord('C'):  # Clear
                self.source_points = []
                current_points.clear()
                circle_radius[0] = 0
            elif k == ord('z') or k == ord('Z'):
                view_scale[0] = min(10.0, view_scale[0] + 0.2)
            elif k == ord('x') or k == ord('X'):
                view_scale[0] = max(0.2, view_scale[0] - 0.2)
            elif k == ord('+') or k == ord('='):  # 加粗
                line_width[0] = min(20, line_width[0] + 1)
            elif k == ord('-') or k == ord('_'):  # 减细
                line_width[0] = max(1, line_width[0] - 1)
            elif k == ord('o') or k == ord('O'):  # 切换圆形模式
                circle_mode[0] = not circle_mode[0]
            elif k == ord('g') or k == ord('G'):  # 调节豁口角度
                gap_angle[0] = (gap_angle[0] + 20) % 180  # 0-160度循环
                if gap_angle[0] < 20:
                    gap_angle[0] = 20
            elif k == ord('r') or k == ord('R'):  # 重置视图
                offset_x[0], offset_y[0] = 0, 0
                view_scale[0] = min(800 / w, 600 / h, 1.0)
    
    def locate_target(self):
        """定位模特图 - 用画笔圈出眼睛区域（可画多个）"""
        img = self.target_img.copy()
        h, w = img.shape[:2]
        self.target_points = []
        
        view_scale = [min(900 / w, 700 / h, 1.0)]
        offset_x, offset_y = [0], [0]
        drawing = [False]
        dragging = [False]
        moving = [False]
        drag_start = [0, 0]
        move_start = [0, 0]
        current_points = []
        line_width = [3]
        circle_mode = [False]
        circle_center = [0, 0]
        circle_radius = [0]
        gap_angle = [60]
        append_mode = [False]  # 追加模式：新画的线追加到上一个区域
        
        def mouse_cb(event, x, y, flags, param):
            ox = int((x - offset_x[0]) / view_scale[0])
            oy = int((y - offset_y[0]) / view_scale[0])
            
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing[0] = True
                if circle_mode[0]:
                    circle_center[0], circle_center[1] = ox, oy
                    circle_radius[0] = 0
                else:
                    current_points.clear()
                    current_points.append([ox, oy])
            elif event == cv2.EVENT_MOUSEMOVE:
                if drawing[0]:
                    if circle_mode[0]:
                        dx, dy = ox - circle_center[0], oy - circle_center[1]
                        circle_radius[0] = int(np.sqrt(dx*dx + dy*dy))
                    else:
                        current_points.append([ox, oy])
                elif dragging[0]:
                    offset_x[0] = x - drag_start[0]
                    offset_y[0] = y - drag_start[1]
                elif moving[0] and len(self.target_points) > 0:
                    dx = ox - move_start[0]
                    dy = oy - move_start[1]
                    self.target_points[-1] = [[p[0]+dx, p[1]+dy] for p in self.target_points[-1]]
                    move_start[0], move_start[1] = ox, oy
            elif event == cv2.EVENT_LBUTTONUP:
                drawing[0] = False
                if circle_mode[0] and circle_radius[0] > 5:
                    pts = []
                    gap_half = gap_angle[0] / 2
                    start_deg = -90 + gap_half
                    end_deg = -90 - gap_half + 360
                    num_pts = 60
                    for i in range(num_pts + 1):
                        deg = start_deg + (end_deg - start_deg) * i / num_pts
                        a = np.radians(deg)
                        px = int(circle_center[0] + circle_radius[0] * np.cos(a))
                        py = int(circle_center[1] + circle_radius[0] * np.sin(a))
                        pts.append([px, py])
                    self.target_points.append(pts)
                    circle_radius[0] = 0
                elif len(current_points) > 10:
                    if append_mode[0] and len(self.target_points) > 0:
                        # 追加到最后一个区域
                        self.target_points[-1].extend(current_points.copy())
                    else:
                        self.target_points.append(current_points.copy())
                current_points.clear()
            elif event == cv2.EVENT_RBUTTONDOWN:
                dragging[0] = True
                drag_start[0] = x - offset_x[0]
                drag_start[1] = y - offset_y[0]
            elif event == cv2.EVENT_RBUTTONUP:
                dragging[0] = False
            elif event == cv2.EVENT_MBUTTONDOWN:
                moving[0] = True
                move_start[0], move_start[1] = ox, oy
            elif event == cv2.EVENT_MBUTTONUP:
                moving[0] = False
            elif event == cv2.EVENT_MOUSEWHEEL:  # 滚轮调整最后一个区域的大小
                if len(self.target_points) > 0:
                    region = self.target_points[-1]
                    cx = sum(p[0] for p in region) // len(region)
                    cy = sum(p[1] for p in region) // len(region)
                    scale = 1.05 if flags > 0 else 0.95
                    self.target_points[-1] = [[int(cx + (p[0]-cx)*scale), int(cy + (p[1]-cy)*scale)] 
                                               for p in region]
        
        def draw():
            disp = img.copy()
            lw = line_width[0]
            
            # 画圆形预览（带豁口）
            if circle_mode[0] and drawing[0] and circle_radius[0] > 0:
                gap_half = gap_angle[0] / 2
                start_a = int(-90 + gap_half)
                end_a = int(-90 - gap_half + 360)
                cv2.ellipse(disp, (circle_center[0], circle_center[1]), 
                           (circle_radius[0], circle_radius[0]), 0, start_a, end_a, (0, 255, 0), lw)
            elif len(current_points) > 1:
                pts = np.array(current_points, dtype=np.int32)
                cv2.polylines(disp, [pts], False, (0, 255, 0), lw)
            
            # 画所有已确定的区域
            for i, region in enumerate(self.target_points):
                if len(region) > 1:
                    pts = np.array(region, dtype=np.int32)
                    cv2.polylines(disp, [pts], False, (0, 255, 0), lw)  # 不闭合
                    cx = sum(p[0] for p in region) // len(region)
                    cy = sum(p[1] for p in region) // len(region)
                    cv2.putText(disp, str(i+1), (cx-10, cy+10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            scaled = cv2.resize(disp, (int(w * view_scale[0]), int(h * view_scale[0])))
            
            canvas_h, canvas_w = 750, 1000
            canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
            canvas[:] = (40, 40, 40)
            
            sh, sw = scaled.shape[:2]
            px, py = int(offset_x[0]), int(offset_y[0])
            
            src_x1, src_y1 = max(0, -px), max(0, -py)
            src_x2, src_y2 = min(sw, canvas_w - px), min(sh, canvas_h - py)
            dst_x1, dst_y1 = max(0, px), max(0, py)
            dst_x2 = dst_x1 + (src_x2 - src_x1)
            dst_y2 = dst_y1 + (src_y2 - src_y1)
            
            if src_x2 > src_x1 and src_y2 > src_y1:
                canvas[dst_y1:dst_y2, dst_x1:dst_x2] = scaled[src_y1:src_y2, src_x1:src_x2]
            
            mode_str = "CIRCLE" if circle_mode[0] else ("APPEND" if append_mode[0] else "FREE")
            color = (0, 255, 0) if append_mode[0] else (0, 255, 255)
            cv2.putText(canvas, f"Eyes: {len(self.target_points)} | Mode: {mode_str} | Middle: Move | Scroll: Resize", 
                       (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)
            cv2.putText(canvas, f"[O] Circle  [A] Append  [G] Gap:{gap_angle[0]}  [U] Undo  [SPACE] OK", 
                       (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            return canvas
        
        win = 'Step2: Draw Eye Areas'
        cv2.namedWindow(win, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(win, mouse_cb)
        
        while True:
            cv2.imshow(win, draw())
            k = cv2.waitKey(30)
            
            if k == -1:
                continue
            k = k & 0xFF
            
            if k == 32:  # SPACE
                if len(self.target_points) > 0:
                    cv2.destroyAllWindows()
                    # 询问是否保存到历史记录
                    self.ask_save_target_history()
                    return True
            elif k == 27 or k == ord('q'):  # ESC
                cv2.destroyAllWindows()
                return False
            elif k == ord('u') or k == ord('U'):  # Undo last
                if self.target_points:
                    self.target_points.pop()
            elif k == ord('c') or k == ord('C'):  # Clear all
                self.target_points = []
                current_points.clear()
                circle_radius[0] = 0
            elif k == ord('z') or k == ord('Z'):
                view_scale[0] = min(10.0, view_scale[0] + 0.2)
            elif k == ord('x') or k == ord('X'):
                view_scale[0] = max(0.2, view_scale[0] - 0.2)
            elif k == ord('+') or k == ord('='):  # 加粗
                line_width[0] = min(20, line_width[0] + 1)
            elif k == ord('-') or k == ord('_'):  # 减细
                line_width[0] = max(1, line_width[0] - 1)
            elif k == ord('o') or k == ord('O'):  # 切换圆形模式
                circle_mode[0] = not circle_mode[0]
                if circle_mode[0]:
                    append_mode[0] = False  # 圆形模式下关闭追加
            elif k == ord('a') or k == ord('A'):  # 切换追加模式
                append_mode[0] = not append_mode[0]
                if append_mode[0]:
                    circle_mode[0] = False  # 追加模式下关闭圆形
            elif k == ord('g') or k == ord('G'):  # 调节豁口角度
                gap_angle[0] = (gap_angle[0] + 20) % 180
                if gap_angle[0] < 20:
                    gap_angle[0] = 20
            elif k == ord('r') or k == ord('R'):  # 重置视图
                offset_x[0], offset_y[0] = 0, 0
                view_scale[0] = min(900 / w, 700 / h, 1.0)
    
    def process(self):
        """处理并生成结果 - 使用画笔圈选的区域"""
        if len(self.source_points) < 10 or len(self.target_points) == 0:
            return None
        
        # 从源图圈选区域提取纹理
        sh, sw = self.source_img.shape[:2]
        source_pts = np.array(self.source_points, dtype=np.int32)
        
        # 创建源蒙版
        source_mask = np.zeros((sh, sw), dtype=np.uint8)
        cv2.fillPoly(source_mask, [source_pts], 255)
        
        # 获取边界框
        sx, sy, srw, srh = cv2.boundingRect(source_pts)
        
        # 提取纹理区域
        cropped = self.source_img[sy:sy+srh, sx:sx+srw].copy()
        cropped_mask = source_mask[sy:sy+srh, sx:sx+srw]
        
        # 创建带羽化的alpha通道
        feather = 15
        alpha = cv2.GaussianBlur(cropped_mask.astype(np.float32), (feather*2+1, feather*2+1), 0)
        alpha = alpha / alpha.max() if alpha.max() > 0 else alpha
        
        # 创建带alpha的纹理
        texture = np.dstack([cropped, (alpha * 255).astype(np.uint8)])
        
        # 应用到每个目标区域
        result = self.target_img.copy()
        
        for target_region in self.target_points:
            if len(target_region) < 10:
                continue
            
            target_pts = np.array(target_region, dtype=np.int32)
            tx, ty, trw, trh = cv2.boundingRect(target_pts)
            
            # 创建目标蒙版
            th, tw = result.shape[:2]
            target_mask = np.zeros((th, tw), dtype=np.uint8)
            cv2.fillPoly(target_mask, [target_pts], 255)
            target_cropped_mask = target_mask[ty:ty+trh, tx:tx+trw]
            
            # 羽化目标蒙版
            target_alpha = cv2.GaussianBlur(target_cropped_mask.astype(np.float32), (feather*2+1, feather*2+1), 0)
            target_alpha = target_alpha / target_alpha.max() if target_alpha.max() > 0 else target_alpha
            
            # 缩放纹理以匹配目标区域大小
            scaled_texture = cv2.resize(texture, (trw, trh))
            
            # 混合
            roi = result[ty:ty+trh, tx:tx+trw].astype(np.float32)
            tex_bgr = scaled_texture[:,:,:3].astype(np.float32)
            tex_alpha = scaled_texture[:,:,3:4].astype(np.float32) / 255.0
            
            # 合并源alpha和目标alpha
            combined_alpha = tex_alpha[:,:,0] * target_alpha
            combined_alpha = combined_alpha[:,:,np.newaxis]
            
            # 排除高光区域
            gray = cv2.cvtColor(scaled_texture[:,:,:3], cv2.COLOR_BGR2GRAY)
            highlight = (gray > 210).astype(np.float32)
            highlight = cv2.GaussianBlur(highlight, (9, 9), 0)[:,:,np.newaxis]
            combined_alpha = combined_alpha * (1 - highlight)
            
            # 混合
            blended = tex_bgr * combined_alpha + roi * (1 - combined_alpha)
            result[ty:ty+trh, tx:tx+trw] = np.clip(blended, 0, 255).astype(np.uint8)
        
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
