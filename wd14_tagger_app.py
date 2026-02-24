"""
优可WD14打标器 - NiceGUI 版本
基于WD14tagger的图像打标工具
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from nicegui import ui, app, run
from nicegui.events import UploadEventArguments

import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

# 默认配置
DEFAULT_MODEL = "wd-convnext-tagger-v3"
DEFAULT_OUTPUT_DIR = "./output"
CONFIG_FILE = "./config.json"
MODEL_DIR = "F:\优可WD14打标器\models"
DEFAULT_PORT = 7960  # 默认端口

# 全局状态
class AppState:
    def __init__(self):
        self.image_paths: List[str] = []
        self.selected_indices: set = set()
        self.is_processing = False
        self.model_sessions: Dict[str, ort.InferenceSession] = {}
        self.tag_data: Dict[str, Tuple[List[str], List[str]]] = {}
        # 国际化相关 - 延迟加载语言设置
        self._current_lang = None  # 使用私有变量，通过属性延迟加载
        self.ui_refs = {}  # 存储UI元素引用
        # 文本字典
        self.TEXTS = {
            'zh': {
                'app_title': '优可WD14打标器',
                'app_subtitle': '基于WD14tagger的图像打标工具',
                'uploaded_images': '☑️ 已上传图片 (点击选择)',
                'processing_progress': '📝 打标进度',
                'waiting_for_processing': '等待开始处理...',
                'image_upload': '📁 图片上传',
                'add_images': '➕ 添加图片',
                'image_management': '🗑️ 图片管理',
                'delete_selected': '删除选中',
                'clear_all': '清空全部',
                'settings': '⚙️ 设置',
                'model_selection': '模型选择',
                'refresh_models': '🔄 刷新模型',
                'confidence_threshold': '置信度阈值',
                'current_value': '当前值: {value}',
                'output_path': '输出路径',
                'open_output_folder': '📂 打开输出文件夹',
                'start_processing': '🚀 开始打标',
                'select_images_first': '请先选择图片',
                'select_images': '选择图片',
                'processing_started': '开始处理...',
                'processing_completed': '处理完成!',
                'completed': '已完成',
                'skipped': '已跳过',
                'failed': '失败',
                'files_uploaded': '共 {count} 张图片，选中 {selected} 张',
                'language': '语言',
                'chinese': '中文',
                'english': 'English',
                'switched_to': '已切换到 {lang}',
                'switched_to_en': 'Switched to {lang}',
                'created_folder_failed': '创建文件夹失败: {error}',
                'opened_output_folder': '已打开输出文件夹',
                'open_failed': '打开失败: {error}',
                'added_images': '已添加 {count} 张图片',
                'no_images_selected': '请选择要删除的图片',
                'selected_images_deleted': '已删除 {count} 张选中的图片',
                'all_images_cleared': '已清空所有图片',
                'models_refreshed': '模型列表已刷新',
                'processing_image': '处理中: {image}',
                'skipped_existing': '已跳过 (txt已存在): {file}',
                'retagged': '重新打标: {file}',
                'processing_failed': '处理失败: {error}',
                'error': '错误',
                'success': '成功',
                'file_added': '已添加: {name}',
                'please_select_images_to_delete': '请先选择要删除的图片',
                'images_deleted': '已删除 {count} 张图片',
                'please_upload_images_first': '请先上传图片',
                'processing_in_progress': '正在处理中，请稍候...',
                'final_result': '最终统计: 完成 {completed} 个, 跳过 {skipped} 个, 失败 {failed} 个',
                'no_images': '暂无图片，请添加图片',
            },
            'en': {
                'app_title': 'Youkengi WD14 Tagger',
                'app_subtitle': 'Image tagging tool based on WD14tagger',
                'uploaded_images': '☑️ Uploaded Images (Click to select)',
                'processing_progress': '📝 Processing Progress',
                'waiting_for_processing': 'Waiting for processing...',
                'image_upload': '📁 Image Upload',
                'add_images': '➕ Add Images',
                'image_management': '🗑️ Image Management',
                'delete_selected': 'Delete Selected',
                'clear_all': 'Clear All',
                'settings': '⚙️ Settings',
                'model_selection': 'Model Selection',
                'refresh_models': '🔄 Refresh Models',
                'confidence_threshold': 'Confidence Threshold',
                'current_value': 'Current value: {value}',
                'output_path': 'Output Path',
                'open_output_folder': '📂 Open Output Folder',
                'start_processing': '🚀 Start Tagging',
                'select_images_first': 'Please select images first',
                'select_images': 'Select Images',
                'processing_started': 'Processing started...',
                'processing_completed': 'Processing completed!',
                'completed': 'Completed',
                'skipped': 'Skipped',
                'failed': 'Failed',
                'files_uploaded': 'Total {count} images, selected {selected}',
                'language': 'Language',
                'chinese': '中文',
                'english': 'English',
                'switched_to': 'Switched to {lang}',
                'switched_to_en': 'Switched to {lang}',
                'created_folder_failed': 'Failed to create folder: {error}',
                'opened_output_folder': 'Output folder opened',
                'open_failed': 'Failed to open: {error}',
                'added_images': 'Added {count} images',
                'no_images_selected': 'Please select images to delete',
                'selected_images_deleted': 'Deleted {count} selected images',
                'all_images_cleared': 'Cleared all images',
                'models_refreshed': 'Model list refreshed',
                'processing_image': 'Processing: {image}',
                'skipped_existing': 'Skipped (txt exists): {file}',
                'retagged': 'Retagged: {file}',
                'processing_failed': 'Processing failed: {error}',
                'error': 'Error',
                'success': 'Success',
                'file_added': 'Added: {name}',
                'please_select_images_to_delete': 'Please select images to delete first',
                'images_deleted': 'Deleted {count} images',
                'please_upload_images_first': 'Please upload images first',
                'processing_in_progress': 'Processing in progress, please wait...',
                'final_result': 'Final result: {completed} completed, {skipped} skipped, {failed} failed',
                'no_images': 'No images, please add images',
            }
        }
    
    @property
    def current_lang(self):
        """获取当前语言，首次访问时从配置加载"""
        if self._current_lang is None:
            self._current_lang = get_last_language()
        return self._current_lang
    
    @current_lang.setter
    def current_lang(self, value):
        """设置当前语言"""
        self._current_lang = value
    
    def t(self, key, **kwargs):
        """获取当前语言的文本"""
        text = self.TEXTS[self.current_lang].get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

state = AppState()


def load_config() -> dict:
    """加载配置文件"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    return {}


def save_config(config: dict):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置文件失败: {e}")


def get_last_model() -> str:
    """获取上次使用的模型"""
    config = load_config()
    return config.get('last_model', DEFAULT_MODEL)


def set_last_model(model: str):
    """设置上次使用的模型"""
    config = load_config()
    config['last_model'] = model
    save_config(config)


def get_output_dir() -> str:
    """获取输出目录"""
    config = load_config()
    return config.get('output_dir', DEFAULT_OUTPUT_DIR)


def set_output_dir(output_dir: str):
    """设置输出目录"""
    config = load_config()
    config['output_dir'] = output_dir
    save_config(config)


def get_threshold() -> float:
    """获取置信度阈值"""
    config = load_config()
    return config.get('threshold', 0.35)


def set_threshold(threshold: float):
    """设置置信度阈值"""
    config = load_config()
    config['threshold'] = threshold
    save_config(config)


def get_last_language() -> str:
    """获取上次使用的语言"""
    config = load_config()
    return config.get('last_language', 'zh')


def set_last_language(lang: str):
    """设置上次使用的语言"""
    config = load_config()
    config['last_language'] = lang
    save_config(config)


def get_wd14_models() -> List[str]:
    """获取WD14tagger模型列表"""
    models = []
    if os.path.exists(MODEL_DIR):
        for item in os.listdir(MODEL_DIR):
            model_path = os.path.join(MODEL_DIR, item)
            if os.path.isdir(model_path) and os.path.exists(os.path.join(model_path, "model.onnx")):
                models.append(item)
    return models if models else [DEFAULT_MODEL]


def load_wd14_model(model_name: str) -> Tuple[Optional[ort.InferenceSession], Optional[Tuple[List[str], List[str]]]]:
    """加载WD14tagger模型"""
    model_path = os.path.join(MODEL_DIR, model_name, "model.onnx")
    tags_path = os.path.join(MODEL_DIR, model_name, "selected_tags.csv")
    
    if not os.path.exists(model_path):
        print(f"模型文件不存在: {model_path}")
        return None, None
    
    if not os.path.exists(tags_path):
        print(f"标签文件不存在: {tags_path}")
        return None, None
    
    try:
        # 加载模型
        session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        
        # 加载标签
        general_tags = []
        character_tags = []
        with open(tags_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('tag_id'):
                    parts = line.split(',')
                    if len(parts) >= 4:
                        tag = parts[1].strip()
                        category = int(parts[2])
                        if category == 0:
                            general_tags.append(tag)
                        elif category == 4:
                            character_tags.append(tag)
        
        return session, (general_tags, character_tags)
    except Exception as e:
        print(f"加载模型失败: {e}")
        return None, None


def preprocess_image(image_path: str, size: Tuple[int, int] = (448, 448)) -> np.ndarray:
    """预处理图片"""
    try:
        image = Image.open(image_path).convert('RGB')
        
        # 转换为BGR格式（参考代码使用的格式）
        image_array = np.array(image, dtype=np.float32)
        image_array = image_array[:, :, ::-1]  # RGB -> BGR
        
        # 填充为正方形
        h, w, _ = image_array.shape
        size_max = max(h, w)
        pad_x = size_max - w
        pad_y = size_max - h
        pad_l = pad_x // 2
        pad_t = pad_y // 2
        image_array = np.pad(image_array, ((pad_t, pad_y - pad_t), (pad_l, pad_x - pad_l), (0, 0)), 
                           mode='constant', constant_values=255)
        
        # 调整大小
        interp = cv2.INTER_AREA if size_max > size[0] else cv2.INTER_LANCZOS4
        image_array = cv2.resize(image_array, size, interpolation=interp)
        
        # 添加batch维度
        image_array = np.expand_dims(image_array, axis=0)
        return image_array
    except Exception as e:
        print(f"预处理图片失败: {e}")
        return None


def get_image_tags(image_path: str, model_name: str, threshold: float = 0.35) -> Tuple[str, str]:
    """获取图片标签"""
    # 每次都重新加载模型，确保使用正确的模型
    session, tag_data = load_wd14_model(model_name)
    if not session or not tag_data:
        return "Error: 模型加载失败", ""
    
    general_tags, character_tags = tag_data
    
    # 预处理图片
    image_array = preprocess_image(image_path)
    if image_array is None:
        return "Error: 图片预处理失败", ""
    
    try:
        # 推理
        input_name = session.get_inputs()[0].name
        
        # 确保输入形状正确
        if image_array.shape != tuple(session.get_inputs()[0].shape):
            if len(session.get_inputs()[0].shape) == 4:
                # 检查是否需要调整通道顺序
                if session.get_inputs()[0].shape[1] == 3:  # CHW format
                    image_array = image_array.transpose(0, 3, 1, 2)  # NHWC -> NCHW
        
        # 执行推理
        outputs = session.run(None, {input_name: image_array})
        
        # 处理输出
        general_output = outputs[0][0]
        character_output = outputs[1][0] if len(outputs) > 1 else []
        
        # 过滤标签
        tags = []
        # 跳过前4个评分标签（参考代码中的处理方式）
        start_idx = 4
        
        for i in range(start_idx, len(general_output)):
            score = general_output[i]
            if score >= threshold and i - start_idx < len(general_tags):
                tag = general_tags[i - start_idx]
                tags.append(tag)
        
        for i, score in enumerate(character_output):
            if score >= threshold and i < len(character_tags):
                tags.append(character_tags[i])
        
        # 生成英文标签（使用下划线格式）
        english_tags = ", ".join(tags)
        
        return english_tags, ""
    except Exception as e:
        print(f"推理失败: {e}")
        return f"Error: {str(e)}", ""


def save_tags_to_txt(image_path: str, english_tags: str, chinese_description: str, output_dir: str) -> tuple[bool, str]:
    """保存标签到 txt 文件"""
    if not english_tags or english_tags.startswith("Error:"):
        return False, "标签无效或为空"
    
    image_name = os.path.basename(image_path)
    txt_name = os.path.splitext(image_name)[0] + ".txt"
    txt_path = os.path.join(output_dir, txt_name)
    
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as f:
            # 只写入英文标签
            f.write(english_tags.strip())
        return True, txt_path
    except Exception as e:
        return False, str(e)


def on_language_change(e):
    """语言切换回调"""
    # 映射选择值到语言代码 - 使用固定值避免语言切换时的映射问题
    lang_map = {'中文': 'zh', 'English': 'en'}
    state.current_lang = lang_map.get(e.value, 'zh')
    
    # 保存语言设置到配置文件
    set_last_language(state.current_lang)
    
    # 更新所有UI元素
    update_language()
    
    # 显示切换提示
    ui.notify(state.t('switched_to', lang=e.value), type="positive")


def update_language():
    """更新所有UI元素的文本"""
    # 更新头部
    if 'app_title' in state.ui_refs:
        state.ui_refs['app_title'].set_text(state.t('app_title'))
    if 'app_subtitle' in state.ui_refs:
        state.ui_refs['app_subtitle'].set_text(state.t('app_subtitle'))
    
    # 更新左侧面板
    if 'uploaded_images_label' in state.ui_refs:
        state.ui_refs['uploaded_images_label'].set_text(state.t('uploaded_images'))
    if 'processing_progress_label' in state.ui_refs:
        state.ui_refs['processing_progress_label'].set_text(state.t('processing_progress'))
    if 'progress_info' in state.ui_refs:
        current_text = state.ui_refs['progress_info'].value
        if current_text == '等待开始处理...':
            state.ui_refs['progress_info'].set_value(state.t('waiting_for_processing'))
    if 'status_label' in state.ui_refs:
        state.ui_refs['status_label'].set_text(state.t('files_uploaded', 
            count=len(state.image_paths), selected=len(state.selected_indices)))
    
    # 更新右侧面板
    if 'image_upload_label' in state.ui_refs:
        state.ui_refs['image_upload_label'].set_text(state.t('image_upload'))
    if 'add_images_button' in state.ui_refs:
        state.ui_refs['add_images_button'].set_text(state.t('add_images'))
    if 'image_management_label' in state.ui_refs:
        state.ui_refs['image_management_label'].set_text(state.t('image_management'))
    if 'delete_selected_button' in state.ui_refs:
        state.ui_refs['delete_selected_button'].set_text(state.t('delete_selected'))
    if 'clear_all_button' in state.ui_refs:
        state.ui_refs['clear_all_button'].set_text(state.t('clear_all'))
    if 'settings_label' in state.ui_refs:
        state.ui_refs['settings_label'].set_text(state.t('settings'))
    if 'model_selection_label' in state.ui_refs:
        state.ui_refs['model_selection_label'].set_text(state.t('model_selection'))
    if 'refresh_models_button' in state.ui_refs:
        state.ui_refs['refresh_models_button'].set_text(state.t('refresh_models'))
    if 'confidence_threshold_label' in state.ui_refs:
        state.ui_refs['confidence_threshold_label'].set_text(state.t('confidence_threshold'))
    if 'threshold_label' in state.ui_refs:
        current_value = get_threshold()
        state.ui_refs['threshold_label'].set_text(state.t('current_value', value=f'{current_value:.2f}'))
    if 'output_path_label' in state.ui_refs:
        state.ui_refs['output_path_label'].set_text(state.t('output_path'))
    if 'open_output_folder_button' in state.ui_refs:
        state.ui_refs['open_output_folder_button'].set_text(state.t('open_output_folder'))
    if 'start_processing_button' in state.ui_refs:
        state.ui_refs['start_processing_button'].set_text(state.t('start_processing'))


def open_output_folder(output_dir: str):
    """打开输出文件夹"""
    abs_path = os.path.abspath(output_dir)
    if not os.path.exists(abs_path):
        try:
            os.makedirs(abs_path)
        except Exception as e:
            ui.notify(state.t('created_folder_failed', error=e), type="negative")
            return
    
    try:
        if os.name == 'nt':
            subprocess.Popen(f'explorer "{abs_path}"')
        elif os.name == 'posix':
            subprocess.Popen(['open', abs_path])
        ui.notify(state.t('opened_output_folder'), type="positive")
    except Exception as e:
        ui.notify(state.t('open_failed', error=e), type="negative")


# ============ UI 组件 ============

def create_header():
    """创建页面头部"""
    with ui.header().classes('bg-gradient-to-r from-blue-600 to-purple-600 text-white'):
        with ui.row().classes('w-full items-center justify-between px-4 py-3'):
            with ui.row().classes('items-center gap-3'):
                ui.icon('photo_library', size='32px')
                state.ui_refs['app_title'] = ui.label(state.t('app_title')).classes('text-2xl font-bold')
            with ui.row().classes('items-center gap-4'):
                state.ui_refs['app_subtitle'] = ui.label(state.t('app_subtitle')).classes('text-sm opacity-80')
                # 语言切换下拉框 - 使用透明背景与头部融合
                # 根据当前语言设置默认值
                default_lang_value = state.t('chinese') if state.current_lang == 'zh' else state.t('english')
                ui.select(
                    options=[state.t('chinese'), state.t('english')],
                    value=default_lang_value,
                    on_change=on_language_change
                ).classes('min-w-[120px] bg-transparent text-white').props('dark dense outlined')


def create_left_panel():
    """创建左侧面板 - 显示图片预览画廊"""
    global status_label, gallery_grid, progress_info
    
    # 画廊标题
    state.ui_refs['uploaded_images_label'] = ui.label(state.t('uploaded_images')).classes('text-lg font-semibold mb-3')
    
    # 画廊网格容器 - 使用卡片样式
    with ui.card().classes('w-full p-4 min-h-[400px]'):
        # 画廊网格 - 使用响应式列数，图片保持完整显示
        gallery_grid = ui.element('div').classes('w-full grid gap-3')
        gallery_grid.style('grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))')
        
        # 显示画廊内容
        with gallery_grid:
            update_gallery()
    
    # 图片状态
    status_label = ui.label(state.t('files_uploaded', count=len(state.image_paths), selected=len(state.selected_indices))).classes('text-sm text-gray-500 mt-3')
    state.ui_refs['status_label'] = status_label
    
    # 打标处理进度信息框
    with ui.card().classes('w-full p-4 mt-3 bg-blue-50'):
        state.ui_refs['processing_progress_label'] = ui.label(state.t('processing_progress')).classes('text-lg font-semibold mb-2')
        progress_info = ui.textarea(
            value=state.t('waiting_for_processing'),
            placeholder=state.t('waiting_for_processing')
        ).props('readonly filled').classes('w-full').style('min-height: 120px; font-family: monospace; background: white;')
    state.ui_refs['progress_info'] = progress_info


def create_right_panel():
    """创建右侧面板 - 所有功能按钮"""
    with ui.element('div').classes('w-full flex flex-col gap-3'):
        # 上传区域
        with ui.card().classes('w-full p-4'):
            state.ui_refs['image_upload_label'] = ui.label(state.t('image_upload')).classes('text-lg font-semibold mb-3')
            
            # 添加图片按钮 - 使用本地文件选择器
            def open_file_dialog():
                """打开文件选择对话框"""
                from nicegui import native
                import tkinter as tk
                from tkinter import filedialog
                
                root = tk.Tk()
                root.withdraw()  # 隐藏主窗口
                root.attributes('-topmost', True)  # 置顶
                
                files = filedialog.askopenfilenames(
                    title=state.t('select_images'),
                    filetypes=[('图片文件', '*.jpg *.jpeg *.png *.gif *.bmp *.webp')]
                )
                root.destroy()
                
                if files:
                    for file_path in files:
                        if file_path not in state.image_paths:
                            state.image_paths.append(file_path)
                    # 先清除再重新添加，确保更新
                    gallery_grid.clear()
                    update_gallery()
                    ui.update()  # 强制更新整个UI
                    ui.notify(state.t('added_images', count=len(files)), type='positive')
            
            state.ui_refs['add_images_button'] = ui.button(state.t('add_images'), on_click=open_file_dialog).classes('w-full mb-2 bg-blue-500 text-white')
        
        # 图片管理
        with ui.card().classes('w-full p-4'):
            state.ui_refs['image_management_label'] = ui.label(state.t('image_management')).classes('text-lg font-semibold mb-3')
            
            with ui.row().classes('w-full gap-2'):
                state.ui_refs['delete_selected_button'] = ui.button(state.t('delete_selected'), on_click=delete_selected).classes('flex-1 bg-gray-200 text-gray-700')
                state.ui_refs['clear_all_button'] = ui.button(state.t('clear_all'), on_click=clear_all).classes('flex-1 bg-gray-200 text-gray-700')
        
        # 设置区域
        with ui.card().classes('w-full p-4'):
            state.ui_refs['settings_label'] = ui.label(state.t('settings')).classes('text-lg font-semibold mb-3')
            
            # 模型名称
            state.ui_refs['model_selection_label'] = ui.label(state.t('model_selection')).classes('text-sm text-gray-600 mb-1')
            global model_select
            models = get_wd14_models()
            # 获取上次使用的模型，如果不在列表中则使用默认
            last_model = get_last_model()
            if last_model not in models:
                last_model = models[0] if models else DEFAULT_MODEL
            model_select = ui.select(
                options=models,
                value=last_model,
                on_change=lambda e: set_last_model(e.value)
            ).classes('w-full mb-3')
            
            state.ui_refs['refresh_models_button'] = ui.button(state.t('refresh_models'), on_click=refresh_models).classes('w-full bg-gray-100 text-gray-700 mb-3')
            
            # 置信度阈值
            state.ui_refs['confidence_threshold_label'] = ui.label(state.t('confidence_threshold')).classes('text-sm text-gray-600 mb-1')
            global threshold_slider, threshold_label
            threshold = get_threshold()
            threshold_slider = ui.slider(
                min=0.1, max=0.9, step=0.05,
                value=threshold,
                on_change=lambda e: (set_threshold(e.value), threshold_label.set_text(state.t('current_value', value=f'{e.value:.2f}')))
            ).classes('w-full mb-3')
            threshold_label = ui.label(state.t('current_value', value=f'{threshold:.2f}')).classes('text-sm text-gray-500 mb-3')
            state.ui_refs['threshold_label'] = threshold_label
            
            # 输出路径
            state.ui_refs['output_path_label'] = ui.label(state.t('output_path')).classes('text-sm text-gray-600 mb-1')
            global output_input
            output_dir = get_output_dir()
            output_input = ui.input(
                value=output_dir,
                on_change=lambda e: set_output_dir(e.value)
            ).classes('w-full mb-3')
            
            state.ui_refs['open_output_folder_button'] = ui.button(state.t('open_output_folder'), on_click=lambda: open_output_folder(output_input.value)).classes('w-full bg-yellow-100 text-gray-700')
        
        # 处理区域
        with ui.card().classes('w-full p-4'):
            state.ui_refs['start_processing_button'] = ui.button(state.t('start_processing'), on_click=start_processing).classes('w-full bg-blue-500 text-white text-lg py-3')
            
            # 进度条
            global progress_bar
            progress_bar = ui.linear_progress(value=0).classes('w-full mt-3')
            progress_bar.set_visibility(False)
            
            # 状态输出
            global status_output
            status_output = ui.textarea(label='处理状态').classes('w-full mt-3').props('readonly')
            status_output.set_visibility(False)


# ============ 事件处理 ============

def handle_upload(e: UploadEventArguments):
    """处理文件上传"""
    if not e.content:
        return
    
    # 保存上传的文件
    upload_dir = Path('./uploads')
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / e.name
    with open(file_path, 'wb') as f:
        f.write(e.content.read())
    
    if str(file_path) not in state.image_paths:
        state.image_paths.append(str(file_path))
        state.selected_indices.discard(len(state.image_paths) - 1)
    
    update_gallery()
    ui.notify(state.t('file_added', name=e.name), type='positive')


def update_gallery():
    """更新画廊显示"""
    global gallery_grid, status_label
    
    # 检查 gallery_grid 是否存在
    if 'gallery_grid' not in globals() or gallery_grid is None:
        return
    
    # 清除现有内容
    gallery_grid.clear()
    
    # 如果没有图片，显示提示
    if not state.image_paths:
        with gallery_grid:
            ui.label(state.t('no_images')).classes('text-gray-400 col-span-full text-center py-8')
        # 更新状态标签
        if 'status_label' in globals() and status_label is not None:
            status_label.set_text(f'共 0 张图片，选中 0 张')
        return
    
    # 添加图片卡片
    for idx, path in enumerate(state.image_paths):
        is_selected = idx in state.selected_indices
        
        # 创建图片卡片
        card_classes = 'cursor-pointer transition-all duration-200 hover:shadow-lg '
        if is_selected:
            card_classes += 'ring-4 ring-blue-500 shadow-xl'
        else:
            card_classes += 'hover:ring-2 hover:ring-gray-300'
        
        with gallery_grid:
            with ui.card().classes(card_classes).on('click', lambda i=idx: toggle_selection(i)):
                # 全图缩小显示，保持宽高比，object-contain 显示完整图片
                # 将路径转换为绝对路径，确保 NiceGUI 能正确加载
                abs_path = os.path.abspath(path)
                ui.image(abs_path).classes('w-full h-48 object-contain bg-gray-50 rounded')
                # 显示文件名
                ui.label(os.path.basename(path)[:20] + '...' if len(os.path.basename(path)) > 20 else os.path.basename(path)).classes('text-xs text-center mt-1 truncate')
    
    # 更新状态标签
    if 'status_label' in globals() and status_label is not None:
        status_label.set_text(f'共 {len(state.image_paths)} 张图片，选中 {len(state.selected_indices)} 张')


def update_status_label():
    """更新状态标签"""
    global status_label
    if 'status_label' in globals() and status_label is not None:
        status_label.set_text(f'共 {len(state.image_paths)} 张图片，选中 {len(state.selected_indices)} 张')


def toggle_selection(idx: int):
    """切换选择状态"""
    if idx in state.selected_indices:
        state.selected_indices.remove(idx)
    else:
        state.selected_indices.add(idx)
    update_gallery()


def delete_selected():
    """删除选中的图片"""
    if not state.selected_indices:
        ui.notify(state.t('please_select_images_to_delete'), type='warning')
        return
    
    # 按索引降序排序，避免删除时索引变化
    sorted_indices = sorted(state.selected_indices, reverse=True)
    for idx in sorted_indices:
        if 0 <= idx < len(state.image_paths):
            state.image_paths.pop(idx)
    
    # 重新构建选中索引
    state.selected_indices.clear()
    update_gallery()
    ui.notify(state.t('images_deleted', count=len(sorted_indices)), type='positive')


def clear_all():
    """清空所有图片"""
    state.image_paths.clear()
    state.selected_indices.clear()
    update_gallery()
    ui.notify(state.t('all_images_cleared'), type='positive')


def refresh_models():
    """刷新模型列表"""
    models = get_wd14_models()
    model_select.options = models
    model_select.value = models[0] if models else DEFAULT_MODEL
    ui.notify(state.t('models_refreshed'), type='positive')


def check_txt_exists(image_path: str, output_dir: str) -> tuple[bool, bool]:
    """检查对应的 txt 文件是否已存在，以及是否超过1KB
    返回: (是否存在, 是否超过1KB需要重新打标)
    """
    image_name = os.path.basename(image_path)
    txt_name = os.path.splitext(image_name)[0] + ".txt"
    txt_path = os.path.join(output_dir, txt_name)
    # 转换为绝对路径确保一致性
    txt_path = os.path.abspath(txt_path)
    
    print(f"[DEBUG] Checking txt: {txt_path}")
    print(f"[DEBUG] output_dir={output_dir}, image_name={image_name}")
    
    if not os.path.exists(txt_path):
        print(f"[DEBUG] {txt_name} does not exist at {txt_path}")
        return False, False
    
    # 检查文件大小，超过1KB则标记为需要重新打标
    try:
        file_size = os.path.getsize(txt_path)
        print(f"[DEBUG] {txt_name} exists, size={file_size} bytes ({file_size/1024:.2f} KB)")
        if file_size > 1024:  # 1KB = 1024 bytes
            print(f"[DEBUG] {txt_name} size={file_size} bytes > 1KB, needs re-tagging")
            return True, True
    except Exception as e:
        print(f"[DEBUG] Error getting file size for {txt_path}: {e}")
        return True, False
    
    return True, False

async def process_single_image(image_path: str, model: str, threshold: float, output_dir: str, lang: str = 'zh') -> tuple:
    """处理单张图片 - 在线程池中运行避免阻塞 UI"""
    def _process():
        image_name = os.path.basename(image_path)
        txt_name = os.path.splitext(image_name)[0] + ".txt"
        txt_path = os.path.join(output_dir, txt_name)
        
        # 根据语言选择文本
        if lang == 'en':
            skipped_msg = f"Skipped (txt exists): {txt_name}"
            delete_failed_msg = "Failed to delete oversized file: {error}"
            processing_failed_msg = "Processing failed: {error}"
            retagged_msg = "Retagged: {filename}"
        else:
            skipped_msg = f"已跳过 (txt已存在): {txt_name}"
            delete_failed_msg = "删除超大文件失败: {error}"
            processing_failed_msg = "处理失败: {error}"
            retagged_msg = "重新打标: {filename}"
        
        try:
            # 首先检查 txt 文件是否已存在
            exists, needs_retag = check_txt_exists(image_path, output_dir)
            
            if exists and not needs_retag:
                # 文件存在且大小正常，跳过
                return True, skipped_msg
            
            if exists and needs_retag:
                # 文件存在但超过1KB，删除并重新打标
                try:
                    os.remove(txt_path)
                except Exception as e:
                    return False, delete_failed_msg.format(error=e)
            
            # 调用 WD14tagger
            english_tags, chinese_description = get_image_tags(image_path, model, threshold)
            
            if english_tags.startswith('Error:'):
                return False, english_tags
            else:
                success, msg = save_tags_to_txt(image_path, english_tags, chinese_description, output_dir)
                if success and exists and needs_retag:
                    # 如果是重新打标，修改返回消息
                    return True, retagged_msg.format(filename=os.path.basename(msg))
                return success, msg
        except Exception as e:
            return False, processing_failed_msg.format(error=str(e))
    
    return await run.io_bound(_process)

async def start_processing():
    """开始处理图片 - 使用后台线程避免 UI 卡顿"""
    if not state.image_paths:
        ui.notify(state.t('please_upload_images_first'), type='warning')
        return
    
    if state.is_processing:
        ui.notify(state.t('processing_in_progress'), type='warning')
        return
    
    state.is_processing = True
    progress_bar.set_visibility(True)
    status_output.set_visibility(True)
    status_output.value = ''
    
    # 初始化左侧进度信息框
    progress_info.set_value(state.t('processing_started'))
    ui.update(progress_info)
    
    model = model_select.value
    threshold = threshold_slider.value
    output_dir = output_input.value or DEFAULT_OUTPUT_DIR
    print(f"[DEBUG] Output directory: {output_dir}")
    
    results = []
    total = len(state.image_paths)
    processed_count = 0  # 实际处理的图片数（不含跳过）
    
    for idx, image_path in enumerate(state.image_paths):
        # 更新进度
        progress = (idx + 1) / total
        progress_bar.value = progress
        
        image_name = os.path.basename(image_path)
        
        print(f"[DEBUG] Processing {image_name}")
        
        # 在后台线程中处理图片，避免阻塞 UI
        success, msg = await process_single_image(image_path, model, threshold, output_dir, state.current_lang)
        
        # 如果成功处理（不是跳过），增加计数
        if success and '已跳过' not in msg:
            processed_count += 1
        
        # 构建当前图片的处理结果
        current_result = f'[{idx + 1}/{total}] {image_name}'
        if not success:
            current_result += f"\n  ❌ {state.t('failed')}: {msg}"
        elif '已跳过' in msg or 'Skipped' in msg or 'exists' in msg:
            current_result += f"\n  ⏭️ {msg}"
        elif '重新打标' in msg or 'Retagged' in msg:
            current_result += f"\n  🔄 {msg}"
        else:
            current_result += f"\n  ✅ {state.t('completed')}: {os.path.basename(msg)}"
        
        # 添加到结果列表
        results.append(current_result)
        
        # 更新显示 - 包含所有已处理图片的结果
        current_display = '\n\n'.join(results)
        status_output.set_value(current_display)
        progress_info.set_value(current_display)
        ui.update(progress_info)
    
    # 添加完成信息
    completed_count = len([r for r in results if '✅' in r or 'Completed' in r])
    skipped_count = len([r for r in results if '⏭️' in r or 'Skipped' in r])
    failed_count = len([r for r in results if '❌' in r or 'Failed' in r])
    final_display = '\n\n'.join(results) + '\n\n' + state.t('final_result', completed=completed_count, skipped=skipped_count, failed=failed_count)
    status_output.set_value(final_display)
    progress_info.set_value(final_display)
    ui.update(progress_info)
    
    progress_bar.set_visibility(False)
    # 处理完成后5秒隐藏右侧状态输出
    ui.timer(5.0, lambda: status_output.set_visibility(False), once=True)
    state.is_processing = False
    
    ui.notify(state.t('processing_completed'), type='positive')


# ============ 主程序 ============

@ui.page('/')
def main_page():
    """主页面"""
    # 添加 Tailwind CSS
    ui.add_head_html('''
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .gradient-text {
                background: linear-gradient(to right, #3b82f6, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            /* 引导词文本颜色 - 黑色 */
            .prompt-textarea .q-field__native {
                color: #000000 !important;
                font-size: 14px !important;
                line-height: 1.5 !important;
            }
            .prompt-textarea .q-field__control {
                background: white !important;
            }
        </style>
    ''')
    
    create_header()
    
    # 主布局：左右分栏
    with ui.row().classes('w-full p-4 gap-4'):
        # 左侧区域（图片预览区，自适应宽度）
        with ui.column().classes('flex-grow gap-3'):
            create_left_panel()
        
        # 右侧区域（功能按钮区，固定宽度 320px）
        with ui.column().classes('w-80 gap-3 flex-shrink-0'):
            create_right_panel()


if __name__ in {'__main__', '__mp_main__'}:
    import webbrowser
    import threading
    import time
    import socket
    
    def find_available_port(start_port, max_attempts=10):
        """查找可用端口"""
        for i in range(max_attempts):
            port = start_port + i
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    return port
                except OSError:
                    print(f'端口 {port} 已被占用，尝试下一个端口...')
                    continue
        raise RuntimeError(f'无法找到可用端口（尝试了 {max_attempts} 个端口）')
    
    # 查找可用端口
    try:
        available_port = find_available_port(DEFAULT_PORT)
        if available_port != DEFAULT_PORT:
            print(f'默认端口 {DEFAULT_PORT} 被占用，已自动切换到端口 {available_port}')
        else:
            print(f'使用默认端口: {DEFAULT_PORT}')
    except RuntimeError as e:
        print(f'错误: {e}')
        exit(1)
    
    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{available_port}')
        print(f'已自动打开浏览器: http://localhost:{available_port}')
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    print(f'启动 NiceGUI 服务: http://localhost:{available_port}')
    ui.run(
        title='优可WD14打标器',
        host='127.0.0.1',
        port=available_port,
        reload=False,
        show=False  # 不自动打开，我们自己控制
    )
