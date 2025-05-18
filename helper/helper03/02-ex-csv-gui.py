import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.path import Path
import numpy as np
import sys
import os
import math
from matplotlib import font_manager  # 新增导入
from matplotlib.patches import Arrow # 用于绘制箭头

# --- 字体设置 (全局变量) ---
zh_font_prop = None
try:
    # 假设字体文件在脚本同目录下
    script_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(script_dir, 'SimHei.ttf')
    if os.path.exists(font_path):
        zh_font_prop = font_manager.FontProperties(fname=font_path)
        print(f"已成功加载中文字体: {font_path}")
    else:
        print(f"警告：未在目录 '{script_dir}' 下找到字体文件 'SimHei.ttf'，中文可能无法正确显示。")
except NameError:
    # 如果 __file__ 未定义 (例如在某些打包环境中), 尝试当前工作目录
    script_dir = os.getcwd()
    font_path = os.path.join(script_dir, 'SimHei.ttf')
    if os.path.exists(font_path):
        zh_font_prop = font_manager.FontProperties(fname=font_path)
        print(f"已成功加载中文字体: {font_path}")
    else:
        print(f"警告：未在目录 '{script_dir}' 或 '{os.getcwd()}' 下找到字体文件 'SimHei.ttf'，中文可能无法正确显示。")

# --- Constants ---
MINIMAL_DISTANCE = 1e-6 # 用于比较浮点数或角度是否接近零
NORMAL_VECTOR_SCALE = 0.1 # 可视化法线箭头的长度因子

# --- Helper Functions (全局检测函数移到这里) ---

def polygon_signed_area(ys, zs):
    """返回(y,z)多边形的有符号面积；输入无需闭合。"""
    if not ys or not zs or len(ys) < 3:
        return 0.0
    area = 0.0
    n = len(ys)
    for i in range(n):
        j = (i + 1) % n
        area += ys[i] * zs[j] - ys[j] * zs[i]
    return 0.5 * area

def analyse_section_pair(sec_a, sec_b):
    """基于两个 section_data 字典返回问题列表。"""
    issues = []
    # 顶点数量差异
    na = len(sec_a.get("contourY_local_adj", []))
    nb = len(sec_b.get("contourY_local_adj", []))
    if min(na, nb) < 3 or (max(na, nb) > 0 and na > 0 and nb > 0 and min(na, nb) / max(na, nb) < 0.7) :
        issues.append("顶点数量差异过大")
    # 面积比
    area_a = abs(sec_a.get("signed_area", 0.0))
    area_b = abs(sec_b.get("signed_area", 0.0))
    if area_a > 1e-8 and area_b > 1e-8: # 避免除以零或与非常小的面积比较
        if min(area_a, area_b) / max(area_a, area_b) < 0.95:
            issues.append("相邻截面面积差异>5%")
    elif area_a < 1e-8 and area_b > 1e-2: # 一个面积接近零，另一个不是
        issues.append("一个截面面积过小")
    elif area_b < 1e-8 and area_a > 1e-2:
        issues.append("一个截面面积过小")

    # 轮廓方向
    orientation_a = sec_a.get("orientation", 0)
    orientation_b = sec_b.get("orientation", 0)
    if orientation_a != 0 and orientation_b != 0 and orientation_a * orientation_b < 0:
        issues.append("轮廓方向不一致")
    # 极短段转角大
    angle_deg = abs(math.degrees(sec_a.get("curvatureAngle", 0.0)))
    if sec_a.get("length", 1.0) < 0.5 and angle_deg > 20: # 长度单位假设为mm
        issues.append("短段转角>20°")
    return issues

def normalize_vector(vx, vy):
    """归一化向量"""
    norm = np.sqrt(vx**2 + vy**2)
    if norm > MINIMAL_DISTANCE:
        return vx / norm, vy / norm
    else:
        return 1.0, 0.0 # 返回默认值，例如 (1, 0)

def normalize_angle(angle):
    """将角度标准化到 (-pi, pi] 区间"""
    while angle <= -np.pi:
        angle += 2 * np.pi
    while angle > np.pi:
        angle -= 2 * np.pi
    return angle

def calculate_curvature(p1, n1, p2, n2):
    """
    模拟 getCurvatureAngleShift 计算曲率半径和角度。
    输入:
        p1 (tuple): 截面1中心点 (x1, y1)
        n1 (tuple): 截面1单位法线 (nx1, ny1)
        p2 (tuple): 截面2中心点 (x2, y2)
        n2 (tuple): 截面2单位法线 (nx2, ny2)
    输出:
        radius (float): 曲率半径 R (可能为负，表示方向)
        angle (float): 法线夹角 alpha (弧度, 标准化到 (-pi, pi])
    """
    x1, y1 = p1
    nx1, ny1 = n1
    x2, y2 = p2
    nx2, ny2 = n2
    cross_p_n2 = (x2 - x1) * ny2 - (y2 - y1) * nx2
    cross_n2_n1 = nx2 * ny1 - ny2 * nx1
    radius = 0.0
    if abs(cross_n2_n1) > MINIMAL_DISTANCE:
        radius = -cross_p_n2 / cross_n2_n1
    else:
        radius = float('inf') # 使用无穷大表示直线或接近直线
        if abs(nx1 * nx2 + ny1 * ny2 - 1.0) > MINIMAL_DISTANCE: # 检查法线是否几乎平行
             print(f"警告: 曲率计算中法线几乎平行但中心点不同，可能导致问题。N1=({nx1:.3f}, {ny1:.3f}), N2=({nx2:.3f}, {ny2:.3f})")
    angle1 = math.atan2(ny1, nx1)
    angle2 = math.atan2(ny2, nx2)
    angle_diff = angle2 - angle1
    angle = normalize_angle(angle_diff)
    # 增加对半径有效性的检查
    if not math.isfinite(radius):
         # print(f"曲率半径为无穷大，角度设为0. 法线夹角原始值: {math.degrees(angle_diff):.2f}度")
         angle = 0.0 # 如果半径无穷大（直线），角度应为0
    return radius, angle

def rotate_vector(vector, angle_rad):
    """将二维向量旋转指定角度 (弧度)"""
    vx, vy = vector
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    vx_new = cos_a * vx - sin_a * vy
    vy_new = sin_a * vx + cos_a * vy
    return vx_new, vy_new

def calculate_outlet_geometry(s_prime_i, n_hat_i, L_i, R_i, alpha_i):
    """
    模拟 Acoustic3dSimulation::ctrLinePtOut 和出口法线的计算。
    严格遵循 C++ 的条件判断逻辑来计算曲线出口点。
    """
    pt_in_x, pt_in_y = s_prime_i
    norm_in_x, norm_in_y = n_hat_i
    n_vec = (norm_in_x, norm_in_y) # 入口法线向量 N

    # --- 1. 计算出口法线 --- (不变)
    cos_a = math.cos(alpha_i)
    sin_a = math.sin(alpha_i)
    norm_out_x = cos_a * norm_in_x - sin_a * norm_in_y
    norm_out_y = sin_a * norm_in_x + cos_a * norm_in_y
    n_hat_out_i = normalize_vector(norm_out_x, norm_out_y)

    # --- 2. 计算出口中心点 ---
    s_out_i = s_prime_i # 默认等于入口点

    # 只有当段长 L_i 大于阈值时才计算位移
    if L_i > MINIMAL_DISTANCE:
        # 检查是否为直线段 (曲率角接近0 或 曲率半径无穷大)
        if abs(alpha_i) < MINIMAL_DISTANCE or not math.isfinite(R_i):
            # --- 直线情况 ---
            # 切线向量 t = (ny, -nx) (法线顺时针旋转90度)
            tangent_x = norm_in_y
            tangent_y = -norm_in_x
            # 出口点 = 入口点 + 长度 * 单位切线方向
            s_out_x = pt_in_x + L_i * tangent_x
            s_out_y = pt_in_y + L_i * tangent_y
            s_out_i = (s_out_x, s_out_y)
        else:
             # --- 曲线情况 ---
             # 使用曲率半径 R 和转角 alpha 计算出口点
             # 区分 R > 0 (中心在法线左侧) 和 R < 0 (中心在法线右侧)
             # 以及 alpha > 0 (逆时针转) 和 alpha < 0 (顺时针转)

             # 曲率中心 C = s_prime_i + R * n_hat_i
             center_x = pt_in_x + R_i * norm_in_x
             center_y = pt_in_y + R_i * norm_in_y

             # 从曲率中心指向入口点的向量 V_in = s_prime_i - C = -R * n_hat_i
             vec_in_x = -R_i * norm_in_x
             vec_in_y = -R_i * norm_in_y

             # 将 V_in 旋转 -alpha 角度得到指向出口点的向量 V_out
             # 注意：alpha 是从 n_hat_i 到 n_hat_out_i 的角度，
             # 因此从 V_in 到 V_out 需要旋转 -alpha
             vec_out_x, vec_out_y = rotate_vector((vec_in_x, vec_in_y), -alpha_i)

             # 出口点 s_out_i = C + V_out
             s_out_x = center_x + vec_out_x
             s_out_y = center_y + vec_out_y
             s_out_i = (s_out_x, s_out_y)

    return s_out_i, n_hat_out_i


# --- 数据加载与准备 ---
def load_and_prepare_section_data(line_odd, line_even):
    """
    解析CSV行对, 模拟 C++ 中的数据加载、几何中心调整和必要的数据准备。
    返回包含原始和调整后数据的字典。
    """
    local_contour_y = []
    local_contour_z = []
    center_x, center_y = 0.0, 0.0
    normal_x, normal_y = 1.0, 0.0
    scale_in, scale_out = 1.0, 1.0
    try:
        parts_odd = line_odd.strip().split(';')
        if len(parts_odd) < 4: raise ValueError("奇数行字段不足")
        center_x = float(parts_odd[0])
        normal_x = float(parts_odd[1])
        scale_in = float(parts_odd[2]) # 这是 CSV 第三列
        local_contour_y = [float(p) for p in parts_odd[3:] if p.strip()]
    except Exception as e:
        print(f"错误: 解析奇数行失败: {e}\n行: {line_odd.strip()}")
        return None
    try:
        parts_even = line_even.strip().split(';')
        if len(parts_even) < 4: raise ValueError("偶数行字段不足")
        center_y = float(parts_even[0])
        normal_y = float(parts_even[1])
        scale_out = float(parts_even[2]) # 这是 CSV 第三列
        local_contour_z = [float(p) for p in parts_even[3:] if p.strip()]
    except Exception as e:
        print(f"错误: 解析偶数行失败: {e}\n行: {line_even.strip()}")
        return None
    if len(local_contour_y) != len(local_contour_z):
        print(f"错误: 轮廓点数量不匹配 ({len(local_contour_y)} vs {len(local_contour_z)})" )
        return None
    if not local_contour_y:
        print("警告: 未找到轮廓点")

    original_contour_y = list(local_contour_y)
    original_contour_z = list(local_contour_z)
    original_contourY_plot = list(original_contour_y)
    original_contourZ_plot = list(original_contour_z)
    if original_contourY_plot and original_contourZ_plot:
        original_contourY_plot.append(original_contourY_plot[0])
        original_contourZ_plot.append(original_contourZ_plot[0])

    nx_norm, ny_norm = normalize_vector(normal_x, normal_y)
    normalIn_orig = (normal_x, normal_y) 

    z_min_adj, z_max_adj = 0.0, 0.0
    z_c_local = 0.0
    adjusted_contour_z = []
    if local_contour_z:
        z_min_local = min(local_contour_z)
        z_max_local = max(local_contour_z)
        z_c_local = (z_min_local + z_max_local) / 2.0 
        adjusted_contour_z = [z - z_c_local for z in local_contour_z]
        if adjusted_contour_z:
             z_min_adj = min(adjusted_contour_z) 
             z_max_adj = max(adjusted_contour_z)

    adjusted_contour_y = list(local_contour_y) 

    translation_dist = z_c_local * scale_in 
    adjusted_center_x = center_x + translation_dist * nx_norm
    adjusted_center_y = center_y + translation_dist * ny_norm

    ctrLinePtIn_adj = (adjusted_center_x, adjusted_center_y)

    contour_y_plot_adj = list(adjusted_contour_y)
    contour_z_plot_adj = list(adjusted_contour_z)
    if contour_y_plot_adj and contour_z_plot_adj:
        contour_y_plot_adj.append(contour_y_plot_adj[0])
        contour_z_plot_adj.append(contour_z_plot_adj[0])

    y_min_adj, y_max_adj = 0.0, 0.0
    if adjusted_contour_y:
        y_min_adj = min(adjusted_contour_y)
        y_max_adj = max(adjusted_contour_y)

    # 调用全局函数计算面积和方向
    current_signed_area = polygon_signed_area(adjusted_contour_y, adjusted_contour_z)
    current_orientation = 1 if current_signed_area > 0 else (-1 if current_signed_area < 0 else 0)

    return {
        "ctrLinePtIn_adj": ctrLinePtIn_adj,
        "normalIn_adj": (nx_norm, ny_norm), 
        "scaleIn": scale_in,
        "scaleOut": scale_out,
        "contourY_local_adj": adjusted_contour_y, 
        "contourZ_local_adj": adjusted_contour_z, 
        "contourY_plot_adj": contour_y_plot_adj,
        "contourZ_plot_adj": contour_z_plot_adj,
        "original_contourY_plot": original_contourY_plot,
        "original_contourZ_plot": original_contourZ_plot,
        "z_c_local": z_c_local, 
        "zMinAdj_local": z_min_adj, 
        "zMaxAdj_local": z_max_adj, 
        "yMinAdj_local": y_min_adj, 
        "yMaxAdj_local": y_max_adj, 
        "original_center": (center_x, center_y), 
        "normalIn_orig": normalIn_orig, 
        "zMinLocal_orig": min(local_contour_z) if local_contour_z else 0.0,
        "zMaxLocal_orig": max(local_contour_z) if local_contour_z else 0.0,
        "ctrLinePtOut_orig": (center_x, center_y), 
        "normalOut_orig": (nx_norm, ny_norm), 
        "length": 0.0,
        "curvatureRadius": float('inf'),
        "curvatureAngle": 0.0,
        "ctrLinePtOut": ctrLinePtIn_adj, 
        "normalOut": (nx_norm, ny_norm), 
        "signed_area": current_signed_area,
        "orientation": current_orientation,
        "issues": [] # 初始化issues列表
    }

# --- 角点计算 ---
def get_segment_points(section_data_i):
    """
    使用段 i 的 *调整后* 几何数据计算四个角点的全局坐标。
    """
    ptIn = section_data_i["ctrLinePtIn_adj"]
    normalIn = section_data_i["normalIn_adj"] # 使用归一化法线
    scaleIn = section_data_i["scaleIn"]       # 使用入口半径
    # 使用 Z 轴居中后的范围来确定高度
    zmin_local = section_data_i["zMinAdj_local"]
    zmax_local = section_data_i["zMaxAdj_local"]
    ptOut = section_data_i["ctrLinePtOut"] # 使用计算出的出口点
    normalOut = section_data_i["normalOut"] # 使用计算出的出口法线
    scaleOut = section_data_i["scaleOut"]     # 使用出口半径
    # 入口角点
    ptInMin = (ptIn[0] + normalIn[0] * zmin_local * scaleIn,
               ptIn[1] + normalIn[1] * zmin_local * scaleIn)
    ptInMax = (ptIn[0] + normalIn[0] * zmax_local * scaleIn,
               ptIn[1] + normalIn[1] * zmax_local * scaleIn)
    # 出口角点
    ptOutMin = (ptOut[0] + normalOut[0] * zmin_local * scaleOut,
                ptOut[1] + normalOut[1] * zmin_local * scaleOut)
    ptOutMax = (ptOut[0] + normalOut[0] * zmax_local * scaleOut,
                ptOut[1] + normalOut[1] * zmax_local * scaleOut)
    return ptInMin, ptInMax, ptOutMin, ptOutMax

# --- 原始角点计算 (更新) ---
def get_segment_points_original(section_data_i):
    """
    使用段 i 的 *原始* 几何数据计算四个角点的全局坐标。
    """
    ptIn = section_data_i["original_center"]
    normalIn = section_data_i["normalIn_adj"] # 仍使用归一化法线用于方向
    scaleIn = section_data_i["scaleIn"]
    # 使用原始 Z 范围
    zmin_local = section_data_i["zMinLocal_orig"]
    zmax_local = section_data_i["zMaxLocal_orig"]
    # 使用计算出的 *原始* 出口点和法线
    ptOut = section_data_i["ctrLinePtOut_orig"]
    normalOut = section_data_i["normalOut_orig"] # 使用原始出口法线
    scaleOut = section_data_i["scaleOut"]

    ptInMin = (ptIn[0] + normalIn[0] * zmin_local * scaleIn,
               ptIn[1] + normalIn[1] * zmin_local * scaleIn)
    ptInMax = (ptIn[0] + normalIn[0] * zmax_local * scaleIn,
               ptIn[1] + normalIn[1] * zmax_local * scaleIn)
    ptOutMin = (ptOut[0] + normalOut[0] * zmin_local * scaleOut,
                ptOut[1] + normalOut[1] * zmin_local * scaleOut)
    ptOutMax = (ptOut[0] + normalOut[0] * zmax_local * scaleOut,
                ptOut[1] + normalOut[1] * zmax_local * scaleOut)
    return ptInMin, ptInMax, ptOutMin, ptOutMax


# --- GUI Application Class ---
class VocalTractViewerApp:
    def __init__(self, master, font_prop=None):
        self.master = master
        self.font_prop = font_prop
        master.title("声道 CSV 查看器")
        if self.font_prop: master.option_add('*Font', self.font_prop)
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.all_sections_data = []
        self.num_segments = 0
        self.selected_segment_index = -1
        self.adjusted_segment_lines = []
        self.original_segment_lines = [] # 新增
        self.adjusted_normal_arrows = [] # 新增: 存储调整后法线箭头
        self.original_normal_arrows = [] # 新增: 存储原始法线箭头
        self.loaded_csv_basename = ""

        # --- Top Frame for Controls ---
        self.control_frame = tk.Frame(master)
        self.control_frame.pack(side=tk.TOP, fill=tk.X)

        # Load 按钮
        self.btn_load = tk.Button(self.control_frame, text="加载 CSV", command=self.load_csv)
        if self.font_prop: self.btn_load.config(font=self.font_prop)
        self.btn_load.pack(side=tk.LEFT, padx=5, pady=5)

        # Save Plot 按钮
        self.btn_save = tk.Button(self.control_frame, text="保存绘图", command=self.save_plot)
        if self.font_prop: self.btn_save.config(font=self.font_prop)
        self.btn_save["state"] = "disabled"

        # --- Navigation Buttons (新增) ---
        self.btn_prev = tk.Button(self.control_frame, text="< 上一段", command=self.select_prev_segment)
        if self.font_prop: self.btn_prev.config(font=self.font_prop)
        self.btn_prev["state"] = "disabled"

        self.btn_next = tk.Button(self.control_frame, text="下一段 >", command=self.select_next_segment)
        if self.font_prop: self.btn_next.config(font=self.font_prop)
        self.btn_next.pack(side=tk.LEFT, padx=5, pady=5)
        self.btn_next["state"] = "disabled"

        # Status Label
        self.status_label = tk.Label(self.control_frame, text="请加载 CSV 文件开始")
        if self.font_prop: self.status_label.config(font=self.font_prop)
        self.status_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # --- Matplotlib Figure and Axes (改为 1x3) ---
        self.fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        self.ax_left, self.ax_mid, self.ax_right = axes
        self.fig.suptitle("声道可视化", fontproperties=self.font_prop)

        # --- Left Plot (Adjusted Sagittal) Setup ---
        self.ax_left.set_title('调整后矢状面视图', fontproperties=self.font_prop)
        self.ax_left.set_xlabel('全局 X', fontproperties=self.font_prop)
        self.ax_left.set_ylabel('全局 Y', fontproperties=self.font_prop)
        self.ax_left.set_aspect('equal', adjustable='datalim')
        self.ax_left.grid(True)

        # --- Middle Plot (Original Sagittal) Setup (新增) ---
        self.ax_mid.set_title('原始矢状面视图', fontproperties=self.font_prop)
        self.ax_mid.set_xlabel('全局 X', fontproperties=self.font_prop)
        self.ax_mid.set_ylabel('全局 Y', fontproperties=self.font_prop)
        self.ax_mid.set_aspect('equal', adjustable='datalim')
        self.ax_mid.grid(True)

        # --- Right Plot (Cross-section) Setup ---
        self.ax_right.set_title('截面视图 (请选择分段)', fontproperties=self.font_prop)
        self.ax_right.set_xlabel('局部 Y', fontproperties=self.font_prop)
        self.ax_right.set_ylabel('局部 Z', fontproperties=self.font_prop)
        self.ax_right.set_aspect('equal', adjustable='datalim')
        self.ax_right.grid(True)

        # --- Embed Matplotlib in Tkinter ---
        self.canvas = FigureCanvasTkAgg(self.fig, master=master)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # --- Matplotlib Toolbar ---
        self.toolbar = NavigationToolbar2Tk(self.canvas, master)
        self.toolbar.update()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.X)

        # --- Connect Click Event ---
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def on_closing(self):
        """处理窗口关闭事件"""
        # 可以选择在这里添加确认对话框
        # if messagebox.askokcancel("Quit", "Do you want to quit?"):
        print("Closing application...")
        # 清理 matplotlib 图形，防止内存泄漏 (可选但推荐)
        plt.close(self.fig)
        self.master.destroy()

    def load_csv(self):
        filepath = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not filepath:
            return
        self.loaded_csv_basename = os.path.splitext(os.path.basename(filepath))[0]
        self.status_label.config(text=f"Loading: {os.path.basename(filepath)}...")
        self.master.update_idletasks()
        self.all_sections_data = []
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            if len(lines) % 2 != 0: print("Warning: Odd number of lines in CSV.")
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    section = load_and_prepare_section_data(lines[i], lines[i+1])
                    if section: self.all_sections_data.append(section)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process file:\n{e}")
            self.status_label.config(text="Error loading file.")
            self.loaded_csv_basename = ""; self.btn_save["state"] = "disabled"
            return
        if not self.all_sections_data:
            messagebox.showwarning("Warning", "No valid section data found in the file.")
            self.status_label.config(text="No data found.")
            self.loaded_csv_basename = ""; self.btn_save["state"] = "disabled"
            return

        self.num_segments = len(self.all_sections_data) - 1
        if self.num_segments < 0: self.num_segments = 0

        # 计算每个分段的几何属性（长度、曲率、出口点/法线）和潜在问题
        for i in range(self.num_segments):
            data_i = self.all_sections_data[i]
            data_i_plus_1 = self.all_sections_data[i+1]
            s_prime_i = data_i["ctrLinePtIn_adj"]
            s_prime_i_plus_1 = data_i_plus_1["ctrLinePtIn_adj"]
            n_hat_i = data_i["normalIn_adj"]
            n_hat_i_plus_1 = data_i_plus_1["normalIn_adj"]

            # 计算调整后中心线段长度
            length = np.sqrt((s_prime_i_plus_1[0] - s_prime_i[0])**2 + (s_prime_i_plus_1[1] - s_prime_i[1])**2)
            data_i["length"] = length

            # 计算调整后几何的曲率
            radius, angle = calculate_curvature(s_prime_i, n_hat_i, s_prime_i_plus_1, n_hat_i_plus_1)
            data_i["curvatureRadius"] = radius
            data_i["curvatureAngle"] = angle

            # 计算调整后几何的出口点和法线
            s_out_i, n_hat_out_i = calculate_outlet_geometry(
                s_prime_i, n_hat_i, length, radius, angle
            )
            data_i["ctrLinePtOut"] = s_out_i
            data_i["normalOut"] = n_hat_out_i

            # ---- 计算原始几何的属性 ----
            s_orig_i = data_i["original_center"]
            s_orig_i_plus_1 = data_i_plus_1["original_center"]
            n_orig_out_i = rotate_vector(n_hat_i, angle) 
            data_i["normalOut_orig"] = normalize_vector(n_orig_out_i[0], n_orig_out_i[1])

            length_orig = np.sqrt((s_orig_i_plus_1[0] - s_orig_i[0])**2 + (s_orig_i_plus_1[1] - s_orig_i[1])**2)
            s_out_i_orig, _ = calculate_outlet_geometry( 
                 s_orig_i, n_hat_i, length_orig, radius, angle 
            )
            data_i["ctrLinePtOut_orig"] = s_out_i_orig
            
            # ---- 检测问题 ----
            data_i["issues"] = analyse_section_pair(data_i, data_i_plus_1)
            if data_i["issues"]:
                print(f"分段 {i} (截面 {i} 和 {i+1}) 发现问题: {data_i['issues']}")

        self.selected_segment_index = 0 if self.num_segments > 0 else -1
        self.update_plots() 
        self.status_label.config(text=f"已加载 {len(self.all_sections_data)} 个截面 ({self.num_segments} 个分段).")
        self.btn_save["state"] = "normal"
        if self.num_segments > 0:
            self.btn_prev["state"] = "normal"; self.btn_next["state"] = "normal"
        else:
            self.btn_prev["state"] = "disabled"; self.btn_next["state"] = "disabled"

    def save_plot(self):
        """保存当前图形到文件"""
        if not self.all_sections_data:
            messagebox.showwarning("Save Plot", "No data loaded to save.")
            return
        default_filename = f"{self.loaded_csv_basename}_plot"
        if self.selected_segment_index >= 0: default_filename += f"_seg{self.selected_segment_index}"
        default_filename += ".png"
        output_filepath = filedialog.asksaveasfilename(
            title="Save Plot As", initialfile=default_filename, defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf"), ("SVG", "*.svg"), ("All", "*.*")]
        )
        if output_filepath:
            try:
                self.fig.savefig(output_filepath, dpi=300, bbox_inches='tight')
                self.status_label.config(text=f"Plot saved to: {os.path.basename(output_filepath)}")
                print(f"Plot saved successfully to {output_filepath}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save plot:\n{e}")
                self.status_label.config(text="Error saving plot.")

    # --- 修改后的绘图函数，增加法线绘制 ---
    def draw_segment_sagittal_gui(self, ax, section_data_i, segment_index, is_selected):
        ptInMin, ptInMax, ptOutMin, ptOutMax = get_segment_points(section_data_i)
        ptIn = section_data_i["ctrLinePtIn_adj"]
        normalIn = section_data_i["normalIn_adj"]
        
        has_issues = bool(section_data_i.get("issues"))

        color_in = 'orange' if has_issues else ('red' if is_selected else 'gray')
        color_out = 'orange' if has_issues else ('red' if is_selected else 'darkgray')
        color_upper = 'orange' if has_issues else ('red' if is_selected else 'blue')
        color_lower = 'orange' if has_issues else ('red' if is_selected else 'green')
        
        linewidth = 2.0 if is_selected or has_issues else 1.0
        zorder = 16 if has_issues else (15 if is_selected else 5)
        
        lines = []
        lines.extend(ax.plot([ptInMin[0], ptInMax[0]], [ptInMin[1], ptInMax[1]], color=color_in, linestyle='-', linewidth=linewidth, zorder=zorder))
        lines.extend(ax.plot([ptOutMin[0], ptOutMax[0]], [ptOutMin[1], ptOutMax[1]], color=color_out, linestyle='-', linewidth=linewidth, zorder=zorder))
        lines.extend(ax.plot([ptInMin[0], ptOutMin[0]], [ptInMin[1], ptOutMin[1]], color=color_lower, linestyle='-', linewidth=linewidth, zorder=zorder))
        lines.extend(ax.plot([ptInMax[0], ptOutMax[0]], [ptInMax[1], ptOutMax[1]], color=color_upper, linestyle='-', linewidth=linewidth, zorder=zorder))
        
        arrow_len = NORMAL_VECTOR_SCALE * section_data_i.get("scaleIn", 0.1) 
        arrow_fc = 'gold' if has_issues else 'cyan'
        arrow_ec = 'darkorange' if has_issues else 'blue'
        arrow = ax.arrow(ptIn[0], ptIn[1], normalIn[0] * arrow_len, normalIn[1] * arrow_len,
                         head_width=arrow_len*0.3, head_length=arrow_len*0.4, fc=arrow_fc, ec=arrow_ec, zorder=20,
                         label='_nolegend_' if segment_index > 0 else '入口法线')
        return lines, arrow 

    def draw_segment_sagittal_original_gui(self, ax, section_data_i, segment_index, is_selected):
        ptInMin, ptInMax, ptOutMin, ptOutMax = get_segment_points_original(section_data_i)
        ptIn = section_data_i["original_center"]
        normalIn = section_data_i["normalIn_adj"] 
        
        has_issues = bool(section_data_i.get("issues")) # 检查是否存在问题

        color_in = 'orange' if has_issues else ('magenta' if is_selected else 'lightgray')
        color_out = 'orange' if has_issues else ('magenta' if is_selected else 'silver')
        color_upper = 'orange' if has_issues else ('magenta' if is_selected else 'lightblue')
        color_lower = 'orange' if has_issues else ('magenta' if is_selected else 'lightgreen')
        linestyle = '-'
        linewidth = 2.0 if is_selected or has_issues else 1.0
        zorder = 16 if has_issues else (15 if is_selected else 5)

        lines = []
        lines.extend(ax.plot([ptInMin[0], ptInMax[0]], [ptInMin[1], ptInMax[1]], color=color_in, linestyle=linestyle, linewidth=linewidth, zorder=zorder))
        lines.extend(ax.plot([ptOutMin[0], ptOutMax[0]], [ptOutMin[1], ptOutMax[1]], color=color_out, linestyle=linestyle, linewidth=linewidth, zorder=zorder))
        lines.extend(ax.plot([ptInMin[0], ptOutMin[0]], [ptInMin[1], ptOutMin[1]], color=color_lower, linestyle=linestyle, linewidth=linewidth, zorder=zorder))
        lines.extend(ax.plot([ptInMax[0], ptOutMax[0]], [ptInMax[1], ptOutMax[1]], color=color_upper, linestyle=linestyle, linewidth=linewidth, zorder=zorder))
        
        arrow_len = NORMAL_VECTOR_SCALE * section_data_i.get("scaleIn", 0.1)
        arrow_fc = 'gold' if has_issues else 'yellow'
        arrow_ec = 'darkorange' if has_issues else 'orange'
        arrow = ax.arrow(ptIn[0], ptIn[1], normalIn[0] * arrow_len, normalIn[1] * arrow_len,
                         head_width=arrow_len*0.3, head_length=arrow_len*0.4, fc=arrow_fc, ec=arrow_ec, zorder=20,
                         label='_nolegend_' if segment_index > 0 else '原始入口法线')
        return lines, arrow

    def update_adjusted_sagittal_plot(self):
        self.ax_left.clear()
        self.adjusted_segment_lines = []
        self.adjusted_normal_arrows = [] # 清空旧箭头

        if not self.all_sections_data:
            self.ax_left.set_title('调整后矢状面视图 (无数据)', fontproperties=self.font_prop)
            return

        # 先绘制所有未选中的分段
        for i in range(self.num_segments):
            if i != self.selected_segment_index:
                data_i = self.all_sections_data[i]
                lines, arrow = self.draw_segment_sagittal_gui(self.ax_left, data_i, i, False)
                self.adjusted_segment_lines.append(lines)
                self.adjusted_normal_arrows.append(arrow)
                s_prime_i = data_i["ctrLinePtIn_adj"]
                s_out_i = data_i["ctrLinePtOut"]
                self.ax_left.plot([s_prime_i[0], s_out_i[0]], [s_prime_i[1], s_out_i[1]],
                                  color='gray', linestyle='--', marker=None, linewidth=0.8, zorder=9)

        # 最后绘制选中的分段 (使其在最上层)
        if self.selected_segment_index >= 0 and self.selected_segment_index < self.num_segments:
             data_i = self.all_sections_data[self.selected_segment_index]
             lines, arrow = self.draw_segment_sagittal_gui(self.ax_left, data_i, self.selected_segment_index, True)
             self.adjusted_segment_lines.append(lines) # 替换或添加到列表末尾
             self.adjusted_normal_arrows.append(arrow)
             s_prime_i = data_i["ctrLinePtIn_adj"]
             s_out_i = data_i["ctrLinePtOut"]
             self.ax_left.plot([s_prime_i[0], s_out_i[0]], [s_prime_i[1], s_out_i[1]],
                               color='red', linestyle='--', marker='.', markersize=4,
                               linewidth=1.5, zorder=11, label='计算中心线 (选中)')

        # 添加图例（如果需要，可以创建自定义图例项）
        self.ax_left.plot([], [], color='cyan', marker='>', linestyle='None', markersize=5, label='入口法线方向') # 图例占位符
        self.ax_left.set_title('调整后矢状面视图', fontproperties=self.font_prop)
        self.ax_left.set_xlabel('全局 X', fontproperties=self.font_prop)
        self.ax_left.set_ylabel('全局 Y', fontproperties=self.font_prop)
        self.ax_left.set_aspect('equal', adjustable='datalim')
        self.ax_left.grid(True)
        handles, labels = self.ax_left.get_legend_handles_labels()
        # by_label = dict(zip(labels, handles)) # 可能导致重复标签被覆盖
        unique_labels = {}
        for h, l in zip(handles, labels):
            if l not in unique_labels:
                unique_labels[l] = h
        if self.num_segments > 0 and '计算中心线 (选中)' not in unique_labels:
             # 如果没有选中项被绘制，也添加一个灰色中心线图例
             unique_labels['计算中心线'] = plt.Line2D([0],[0], color='gray', linestyle='--', lw=0.8)

        self.ax_left.legend(unique_labels.values(), unique_labels.keys(), fontsize='small', prop=self.font_prop)


    def update_original_sagittal_plot(self):
        self.ax_mid.clear()
        self.original_segment_lines = []
        self.original_normal_arrows = []

        if not self.all_sections_data:
            self.ax_mid.set_title('原始矢状面视图 (无数据)', fontproperties=self.font_prop)
            return

        for i in range(self.num_segments):
            if i != self.selected_segment_index:
                data_i = self.all_sections_data[i]
                lines, arrow = self.draw_segment_sagittal_original_gui(self.ax_mid, data_i, i, False)
                self.original_segment_lines.append(lines)
                self.original_normal_arrows.append(arrow)
                s_prime_i = data_i["original_center"]
                s_out_i = data_i["ctrLinePtOut_orig"]
                self.ax_mid.plot([s_prime_i[0], s_out_i[0]], [s_prime_i[1], s_out_i[1]],
                                  color='darkorange', linestyle=':', marker=None, linewidth=0.8, zorder=9)

        if self.selected_segment_index >= 0 and self.selected_segment_index < self.num_segments:
             data_i = self.all_sections_data[self.selected_segment_index]
             lines, arrow = self.draw_segment_sagittal_original_gui(self.ax_mid, data_i, self.selected_segment_index, True)
             self.original_segment_lines.append(lines)
             self.original_normal_arrows.append(arrow)
             s_prime_i = data_i["original_center"]
             s_out_i = data_i["ctrLinePtOut_orig"]
             self.ax_mid.plot([s_prime_i[0], s_out_i[0]], [s_prime_i[1], s_out_i[1]],
                               color='orange', linestyle=':', marker='x', markersize=4,
                               linewidth=1.5, zorder=11, label='原始中心线 (选中)')

        self.ax_mid.plot([], [], color='yellow', marker='>', linestyle='None', markersize=5, label='入口法线方向')
        self.ax_mid.set_title('原始矢状面视图', fontproperties=self.font_prop)
        self.ax_mid.set_xlabel('全局 X', fontproperties=self.font_prop)
        self.ax_mid.set_ylabel('全局 Y', fontproperties=self.font_prop)
        self.ax_mid.set_aspect('equal', adjustable='datalim')
        self.ax_mid.grid(True)
        handles, labels = self.ax_mid.get_legend_handles_labels()
        # by_label = dict(zip(labels, handles))
        unique_labels = {}
        for h, l in zip(handles, labels):
             if l not in unique_labels: unique_labels[l] = h
        if self.num_segments > 0 and '原始中心线 (选中)' not in unique_labels:
             unique_labels['原始中心线'] = plt.Line2D([0],[0], color='darkorange', linestyle=':', lw=0.8)
        self.ax_mid.legend(unique_labels.values(), unique_labels.keys(), fontsize='small', prop=self.font_prop)

    def update_cross_section_plot(self):
        self.ax_right.clear()
        plot_index = self.selected_segment_index
        if plot_index < 0 and len(self.all_sections_data) > 0:
            plot_index = 0
        elif plot_index < 0:
            self.ax_right.set_title('截面视图 (无数据)', fontproperties=self.font_prop)
            return

        if plot_index >= len(self.all_sections_data):
             self.ax_right.set_title(f'截面视图 (索引 {plot_index} 无效)', fontproperties=self.font_prop)
             return

        section_data = self.all_sections_data[plot_index]
        title_suffix = f" (选中分段入口: {self.selected_segment_index})" if self.selected_segment_index == plot_index and self.num_segments > 0 else " (默认入口)"
        current_title = f'截面 {plot_index}{title_suffix}'

        if section_data.get("original_contourY_plot"):
             self.ax_right.plot(section_data["original_contourY_plot"], section_data["original_contourZ_plot"], marker='.', markersize=3, linestyle='--', color='lightcoral', label='原始轮廓')
        if section_data.get("contourY_plot_adj"):
             self.ax_right.plot(section_data["contourY_plot_adj"], section_data["contourZ_plot_adj"], marker='o', markersize=4, linestyle='-', color='darkblue', label='居中轮廓')
        self.ax_right.axhline(y=0, color='black', linestyle='--', zorder=5, label='局部原点/居中Z')
        z_c = section_data.get("z_c_local")
        if z_c is not None:
             self.ax_right.axhline(y=z_c, color='purple', linestyle='--', zorder=6, label=f'原始Z中心 ({z_c:.2f})')

        self.ax_right.set_title(current_title, fontproperties=self.font_prop)
        self.ax_right.set_xlabel('局部 Y', fontproperties=self.font_prop)
        self.ax_right.set_ylabel('局部 Z', fontproperties=self.font_prop)
        self.ax_right.set_aspect('equal', adjustable='datalim')
        self.ax_right.grid(True)
        handles, labels = self.ax_right.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax_right.legend(by_label.values(), by_label.keys(), fontsize='small', prop=self.font_prop)

        all_x, all_y = [0], [0]
        if section_data.get("original_contourY_plot"): all_x.extend(section_data["original_contourY_plot"])
        if section_data.get("original_contourZ_plot"): all_y.extend(section_data["original_contourZ_plot"])
        if section_data.get("contourY_plot_adj"): all_x.extend(section_data["contourY_plot_adj"])
        if section_data.get("contourZ_plot_adj"): all_y.extend(section_data["contourZ_plot_adj"])
        if z_c is not None: all_y.append(z_c)
        if len(all_x) > 1:
            min_x, max_x = min(all_x), max(all_x); range_x = max_x - min_x or 1.0
            pad_x = 0.1 * range_x + 0.5; self.ax_right.set_xlim(min_x - pad_x, max_x + pad_x)
        if len(all_y) > 1:
            min_y, max_y = min(all_y), max(all_y); range_y = max_y - min_y or 1.0
            pad_y = 0.1 * range_y + 0.5; self.ax_right.set_ylim(min_y - pad_y, max_y + pad_y)

    def print_selected_section_info(self):
        """打印选中分段的起始截面信息到控制台"""
        if self.selected_segment_index < 0 or self.selected_segment_index >= len(self.all_sections_data):
            # 如果是显示最后一个截面或者没有有效选择，则不打印
            if self.selected_segment_index == self.num_segments and self.num_segments >= 0:
                 print(f"\n--- 显示最后一个截面 ({self.num_segments}) 信息 ---")
                 section_data = self.all_sections_data[self.num_segments]
                 # 对于最后一个截面，我们只有入口信息
                 print(f"  截面索引: {self.num_segments}")
                 print(f"  调整后中心点 (Adj Ctr): {section_data['ctrLinePtIn_adj'][0]:.3f}, {section_data['ctrLinePtIn_adj'][1]:.3f}")
                 print(f"  调整后法线 (Adj N):   {section_data['normalIn_adj'][0]:.3f}, {section_data['normalIn_adj'][1]:.3f}")
                 print(f"  原始中心点 (Orig Ctr): {section_data['original_center'][0]:.3f}, {section_data['original_center'][1]:.3f}")
                 # print(f"  原始法线 (Orig N):   {section_data['normalIn_orig'][0]:.3f}, {section_data['normalIn_orig'][1]:.3f}") # 未归一化
                 print(f"  Scale In/Out: {section_data['scaleIn']:.3f} / {section_data['scaleOut']:.3f}")
                 print(f"  局部 Z' 范围 (Adj): {section_data['zMinAdj_local']:.3f} to {section_data['zMaxAdj_local']:.3f} (决定梯形高度)")
                 print(f"  局部 Y' 范围 (Adj): {section_data.get('yMinAdj_local', 'N/A'):.3f} to {section_data.get('yMaxAdj_local', 'N/A'):.3f}")
            else:
                 print("\n未选择有效分段或截面。")
            return

        section_data = self.all_sections_data[self.selected_segment_index]
        print(f"\n--- 选中分段 {self.selected_segment_index} (对应截面 {self.selected_segment_index}) 信息 ---")
        print(f"  调整后中心点 (Adj Ctr): {section_data['ctrLinePtIn_adj'][0]:.3f}, {section_data['ctrLinePtIn_adj'][1]:.3f}")
        print(f"  调整后入口法线 (Adj N_in): {section_data['normalIn_adj'][0]:.3f}, {section_data['normalIn_adj'][1]:.3f}")
        print(f"  调整后出口法线 (Adj N_out):{section_data['normalOut'][0]:.3f}, {section_data['normalOut'][1]:.3f}")
        print(f"  原始中心点 (Orig Ctr): {section_data['original_center'][0]:.3f}, {section_data['original_center'][1]:.3f}")
        # print(f"  原始入口法线 (Orig N_in): {section_data['normalIn_orig'][0]:.3f}, {section_data['normalIn_orig'][1]:.3f}") # 未归一化
        print(f"  计算出的段长 (Length): {section_data['length']:.3f}")
        print(f"  计算出的曲率半径 (R): {section_data['curvatureRadius']:.3f}")
        print(f"  计算出的曲率角度 (Alpha): {math.degrees(section_data['curvatureAngle']):.2f} 度")
        print(f"  Scale In/Out: {section_data['scaleIn']:.3f} / {section_data['scaleOut']:.3f}")
        print(f"  局部 Z' 范围 (Adj): {section_data['zMinAdj_local']:.3f} to {section_data['zMaxAdj_local']:.3f} (决定梯形高度)")
        print(f"  局部 Y' 范围 (Adj): {section_data.get('yMinAdj_local', 'N/A'):.3f} to {section_data.get('yMaxAdj_local', 'N/A'):.3f}")
        print("-" * (20 + len(str(self.selected_segment_index))*2))


    def update_plots(self):
        self.update_adjusted_sagittal_plot()
        self.update_original_sagittal_plot()
        self.update_cross_section_plot()
        self.fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        self.canvas.draw()
        # 打印选中截面信息
        self.print_selected_section_info()

    def on_click(self, event):
        if event.inaxes not in [self.ax_left, self.ax_mid] or not self.all_sections_data or self.num_segments == 0:
            return
        click_x, click_y = event.xdata, event.ydata
        if click_x is None or click_y is None: return
        clicked_segment = -1
        min_dist_sq = float('inf') # 用于处理重叠区域，选择最近的中心点

        # 根据点击的轴选择使用哪个几何数据进行碰撞检测
        target_ax = event.inaxes
        get_points_func = get_segment_points if target_ax == self.ax_left else get_segment_points_original
        center_key = "ctrLinePtIn_adj" if target_ax == self.ax_left else "original_center"

        possible_segments = []
        for i in range(self.num_segments):
            data_i = self.all_sections_data[i]
            pts = get_points_func(data_i)
            poly_path = Path([pts[0], pts[1], pts[3], pts[2], pts[0]]) # 确保是闭合路径
            if poly_path.contains_point((click_x, click_y)):
                 possible_segments.append(i)

        if not possible_segments: return # 没有点中任何分段

        # 如果点中了多个（重叠区域），选择入口中心点离点击位置最近的那个
        if len(possible_segments) > 1:
            for i in possible_segments:
                 center = self.all_sections_data[i][center_key]
                 dist_sq = (click_x - center[0])**2 + (click_y - center[1])**2
                 if dist_sq < min_dist_sq:
                      min_dist_sq = dist_sq
                      clicked_segment = i
        else:
            clicked_segment = possible_segments[0]


        if clicked_segment != -1 and clicked_segment != self.selected_segment_index:
            self.selected_segment_index = clicked_segment
            self.update_plots()
            self.status_label.config(text=f"选中分段: {self.selected_segment_index}")


    def select_prev_segment(self):
        if not self.all_sections_data or self.num_segments <= 0: return
        self.selected_segment_index -= 1
        if self.selected_segment_index < 0: self.selected_segment_index = self.num_segments - 1
        self.update_plots()
        self.status_label.config(text=f"选中分段: {self.selected_segment_index}")

    def select_next_segment(self):
        if not self.all_sections_data or self.num_segments <= 0: return
        self.selected_segment_index += 1
        if self.selected_segment_index >= self.num_segments: self.selected_segment_index = 0
        self.update_plots()
        self.status_label.config(text=f"选中分段: {self.selected_segment_index}")

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = VocalTractViewerApp(root, font_prop=zh_font_prop)
    root.mainloop()
