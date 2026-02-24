"""
TXT 文件管理工具应用
整合了核心组件和应用入口
"""

import os
from pathlib import Path
from typing import List, Optional
from nicegui import ui


class TxtManager:
    """TXT 文件管理工具"""

    # 多语言文本配置
    TEXTS = {
        'zh': {
            'title': '优可打标校验工具',
            'subtitle': '用于示词的人工检验与调整',
            'preview_area': '📝 预览区',
            'save_changes': '💾 保存修改',
            'delete_file': '🗑️ 删除文件',
            'clear_preview': '🧹 清空预览',
            'image_preview': '📷 图片预览',
            'editor_placeholder': '请选择或加载 TXT 文件',
            'load_area': '📤 加载区',
            'load_files': '批量加载 TXT 文件',
            'file_list': '📂 滚动文件列表',
            'sort_by': '排序方式:',
            'sort_time_desc': '按创建时间（最新在前）',
            'sort_time_asc': '按创建时间（最旧在前）',
            'sort_name_asc': '按文件名（A-Z）',
            'sort_name_desc': '按文件名（Z-A）',
            'clear_file_list': '清空文件列表',
            'select_file': '选择 TXT 文件',
            'txt_files': 'TXT 文件',
            'file_loaded': '成功加载 {} 个 TXT 文件',
            'file_saved': '文件已保存',
            'save_failed': '保存失败: {}',
            'file_removed': '文件已从列表中移除',
            'select_first': '请先选择文件',
            'file_list_cleared': '文件列表已清空',
            'sorted_by': '已将文件列表按{}排序',
            'read_failed': '读取文件失败: {}',
            'language': '🌐 语言',
        },
        'en': {
            'title': 'Youkengi Label Verification Tool',
            'subtitle': 'For manual inspection and adjustment of prompts',
            'preview_area': '📝 Preview Area',
            'save_changes': '💾 Save Changes',
            'delete_file': '🗑️ Delete File',
            'clear_preview': '🧹 Clear Preview',
            'image_preview': '📷 Image Preview',
            'editor_placeholder': 'Please select or load a TXT file',
            'load_area': '📤 Load Area',
            'load_files': 'Batch Load TXT Files',
            'file_list': '📂 File List',
            'sort_by': 'Sort by:',
            'sort_time_desc': 'By Time (Newest First)',
            'sort_time_asc': 'By Time (Oldest First)',
            'sort_name_asc': 'By Name (A-Z)',
            'sort_name_desc': 'By Name (Z-A)',
            'clear_file_list': 'Clear File List',
            'select_file': 'Select TXT Files',
            'txt_files': 'TXT Files',
            'file_loaded': 'Successfully loaded {} TXT files',
            'file_saved': 'File saved',
            'save_failed': 'Save failed: {}',
            'file_removed': 'File removed from list',
            'select_first': 'Please select a file first',
            'file_list_cleared': 'File list cleared',
            'sorted_by': 'File list sorted by {}',
            'read_failed': 'Failed to read file: {}',
            'language': '🌐 Language',
        }
    }

    def __init__(self, title: str = "TXT 管理工具"):
        """
        初始化 TXT 管理工具

        Args:
            title: 工具标题
        """
        self.title = title
        self.txt_files: List[str] = []
        self.selected_index: int = -1
        self.ui_refs = {}
        self.file_contents: dict = {}
        self.file_info: dict = {}  # 存储文件信息，包括创建时间
        self.sort_by: str = 'time'  # 默认按创建时间排序
        self.current_lang: str = 'zh'  # 默认中文
        self.lang_elements: dict = {}  # 存储需要更新的UI元素

    def t(self, key: str) -> str:
        """获取当前语言的文本"""
        return self.TEXTS[self.current_lang].get(key, key)

    def create(self):
        """创建 TXT 管理工具界面"""
        # 添加自定义样式
        self._add_custom_styles()
        
        # 创建头部
        self._create_header()
        
        # 创建主内容区 - 左右布局
        with ui.row().classes('w-full p-4 gap-4 items-start'):
            # 左侧：预览区（主要内容区）
            with ui.column().classes('flex-grow gap-3'):
                # 预览卡片
                with ui.card().classes('w-full p-4'):
                    # 预览区标题和操作按钮
                    with ui.row().classes('w-full items-center justify-between mb-3'):
                        self.lang_elements['preview_area'] = ui.label(self.t('preview_area')).classes('text-lg font-semibold')
                        # 操作按钮
                        with ui.row().classes('gap-2'):
                            self.lang_elements['save_btn'] = ui.button(self.t('save_changes'), on_click=self._save_changes).props('color=primary')
                            self.lang_elements['delete_btn'] = ui.button(self.t('delete_file'), on_click=self._delete_file).props('color=negative')
                            self.lang_elements['clear_btn'] = ui.button(self.t('clear_preview'), on_click=self._clear_preview).props('outline')
                    
                    # 图片预览区域
                    self.lang_elements['image_preview'] = ui.label(self.t('image_preview')).classes('text-md font-semibold mb-3')
                    # 独立的图片显示区域
                    with ui.card().classes('w-full bg-gray-50 image-preview-container'):
                        self.ui_refs['gallery'] = ui.image('').classes('w-full h-full')
                        self.ui_refs['gallery'].style('object-fit: contain;')
                    
                    # 文本编辑框
                    self.ui_refs['editor'] = ui.textarea(
                        value='',
                        placeholder=self.t('editor_placeholder'),
                        on_change=self._on_content_change
                    ).props('autogrow').classes('w-full').style('min-height: 400px; font-family: monospace;')

            # 右侧：加载区（固定宽度）
            with ui.column().classes('w-96 gap-3 flex-shrink-0'):
                # 加载按钮卡片
                with ui.card().classes('w-full p-4'):
                    self.lang_elements['load_area'] = ui.label(self.t('load_area')).classes('text-lg font-semibold mb-3')
                    self.lang_elements['load_btn'] = ui.button(self.t('load_files'), on_click=self._load_txt_files).classes('w-full bg-blue-500 text-white')
                
                # 滚动文件列表卡片
                with ui.card().classes('w-full p-4'):
                    self.lang_elements['file_list'] = ui.label(self.t('file_list')).classes('text-sm font-medium mb-2')
                    # 排序方式选择
                    with ui.row().classes('w-full mb-3 items-center gap-2'):
                        self.lang_elements['sort_label'] = ui.label(self.t('sort_by')).classes('text-xs')
                        self.ui_refs['sort_select'] = ui.select(
                            options=[
                                self.t('sort_time_desc'),
                                self.t('sort_time_asc'),
                                self.t('sort_name_asc'),
                                self.t('sort_name_desc')
                            ],
                            value=self.t('sort_time_desc'),
                            on_change=self._on_sort_change
                        ).classes('flex-grow')
                    # 清空文件列表按钮
                    self.lang_elements['clear_list_btn'] = ui.button(self.t('clear_file_list'), on_click=self._clear_file_list).classes('w-full mb-3 bg-gray-200 text-gray-700')
                    # 使用紧凑卡片展示文件列表
                    self.ui_refs['file_cards'] = ui.column().classes('w-full max-h-[576px] overflow-y-auto')

        return self

    def _on_language_change(self, e):
        """语言切换事件"""
        lang_map = {'中文': 'zh', 'English': 'en'}
        self.current_lang = lang_map.get(e.value, 'zh')
        self._update_language()
        ui.notify(f"Language switched to {e.value}" if self.current_lang == 'en' else f"已切换到{e.value}", type='positive')

    def _update_language(self):
        """更新界面语言"""
        # 更新标题和副标题
        if 'title_label' in self.lang_elements:
            self.lang_elements['title_label'].set_text(self.t('title'))
        if 'subtitle_label' in self.lang_elements:
            self.lang_elements['subtitle_label'].set_text(self.t('subtitle'))
        
        # 更新标签类UI元素
        label_keys = [
            'preview_area', 'image_preview', 'load_area', 'file_list', 'sort_by'
        ]
        
        for key in label_keys:
            if key in self.lang_elements:
                self.lang_elements[key].set_text(self.t(key))
        
        # 更新按钮类UI元素 (使用 _props['label'] 或 set_text)
        button_keys = {
            'save_btn': 'save_changes',
            'delete_btn': 'delete_file',
            'clear_btn': 'clear_preview',
            'load_btn': 'load_files',
            'clear_list_btn': 'clear_file_list'
        }
        
        for btn_key, text_key in button_keys.items():
            if btn_key in self.lang_elements:
                self.lang_elements[btn_key].set_text(self.t(text_key))
        
        # 更新排序选项
        if 'sort_select' in self.ui_refs:
            self.ui_refs['sort_select'].options = [
                self.t('sort_time_desc'),
                self.t('sort_time_asc'),
                self.t('sort_name_asc'),
                self.t('sort_name_desc')
            ]
        
        # 更新编辑器placeholder
        if 'editor' in self.ui_refs:
            self.ui_refs['editor'].props(f'placeholder="{self.t("editor_placeholder")}"')

    def _add_custom_styles(self):
        """添加自定义样式"""
        ui.add_head_html('''
            <script src="https://cdn.tailwindcss.com"></script>
            <style>
                /* 紧凑文件列表样式 */
                .compact-file-item {
                    transition: all 0.2s ease;
                }
                .compact-file-item:hover {
                    background-color: #f0f9ff;
                    transform: translateX(4px);
                }
                .compact-file-item .file-name {
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: #000000;
                }
                .compact-file-item .file-path {
                    font-size: 0.75rem;
                    color: #6b7280;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                /* 预览区文本样式 */
                .q-field textarea {
                    color: #000000 !important;
                    font-family: monospace !important;
                }
                /* 图片预览自适应 - 显示全图 */
                .image-preview-container {
                    width: 100% !important;
                    height: auto !important;
                    min-height: 300px !important;
                    max-height: 600px !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    overflow: hidden !important;
                }
                .image-preview-container img {
                    max-width: 100% !important;
                    max-height: 580px !important;
                    width: auto !important;
                    height: auto !important;
                    object-fit: contain !important;
                }
            </style>
        ''')

    def _create_header(self):
        """创建页面头部"""
        with ui.header().classes('bg-gradient-to-r from-blue-600 to-purple-600 text-white'):
            with ui.row().classes('w-full items-center justify-between px-4 py-3'):
                with ui.row().classes('items-center gap-3'):
                    ui.icon('description', size='32px')
                    self.lang_elements['title_label'] = ui.label(self.t('title')).classes('text-2xl font-bold')
                # 右侧：语言切换 + 副标题
                with ui.row().classes('items-center gap-4'):
                    # 语言切换下拉框
                    with ui.row().classes('items-center gap-2'):
                        ui.label('🌐').classes('text-lg')
                        ui.select(
                            options=['中文', 'English'],
                            value='中文',
                            on_change=self._on_language_change,
                            label='Language'
                        ).classes('min-w-[120px]').props('dark dense outlined')
                    # 副标题
                    self.lang_elements['subtitle_label'] = ui.label(self.t('subtitle')).classes('text-sm opacity-80')

    async def _load_txt_files(self):
        """加载 TXT 文件（异步方式）"""
        import asyncio
        
        # 使用 run_in_executor 避免阻塞主线程
        loop = asyncio.get_event_loop()
        files = await loop.run_in_executor(None, self._open_file_dialog)

        if files:
            # 去重并添加新文件
            for file_path in files:
                if file_path not in self.txt_files:
                    self.txt_files.append(file_path)
                    # 读取文件内容
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        self.file_contents[file_path] = content
                        # 存储文件信息，包括创建时间
                        file_stat = os.stat(file_path)
                        self.file_info[file_path] = {
                            'name': os.path.basename(file_path),
                            'created_time': file_stat.st_ctime
                        }
                    except Exception as e:
                        ui.notify(self.t('read_failed').format(e), type='negative')
            
            # 保存当前选中的文件路径
            current_selected_file = None
            if self.selected_index >= 0 and self.selected_index < len(self.txt_files):
                current_selected_file = self.txt_files[self.selected_index]
            
            # 排序文件列表
            self._sort_files()
            
            # 恢复选中状态
            if current_selected_file and current_selected_file in self.txt_files:
                self.selected_index = self.txt_files.index(current_selected_file)
            
            # 更新文件列表
            self._update_file_list()
            ui.notify(self.t('file_loaded').format(len(files)), type='positive')
    
    def _open_file_dialog(self):
        """打开文件选择对话框"""
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        files = filedialog.askopenfilenames(
            title=self.t('select_file'),
            filetypes=[(self.t('txt_files'), '*.txt')]
        )
        root.destroy()
        return files

    def _update_file_list(self):
        """更新文件列表"""
        # 更新文件卡片列表
        if 'file_cards' in self.ui_refs:
            # 清空现有卡片
            self.ui_refs['file_cards'].clear()
            # 添加新卡片
            for file_path in self.txt_files:
                file_name = os.path.basename(file_path)
                # 检查是否是当前选中的文件
                is_selected = False
                if self.selected_index >= 0 and self.selected_index < len(self.txt_files):
                    is_selected = (file_path == self.txt_files[self.selected_index])
                
                # 使用紧凑样式的卡片，为选中的文件添加特殊样式
                card_classes = 'w-full mb-2 compact-file-item cursor-pointer border-l-4 border-blue-500'
                if is_selected:
                    card_classes += ' bg-blue-50 border-l-4 border-blue-600'
                
                # 使用 parent 参数指定父容器
                with self.ui_refs['file_cards']:
                    card = ui.card().classes(card_classes)
                    with card:
                        if is_selected:
                            ui.label('✅  ' + file_name).classes('file-name text-black font-semibold')
                        else:
                            ui.label(file_name).classes('file-name text-black')
                        ui.label(file_path).classes('file-path text-gray-600')
                    # 添加点击事件
                    card.on('click', lambda e, fp=file_path: self._on_file_click(fp))

    def _on_file_click(self, file_path):
        """文件卡片点击事件"""
        # 保存上一次选中的文件
        self.last_selected_file = file_path
        
        self.selected_index = self.txt_files.index(file_path)
        # 显示文件内容
        if file_path in self.file_contents:
            self.ui_refs['editor'].value = self.file_contents[file_path]
        # 加载同名图片到图片预览区
        self._load_image_preview(file_path)
        # 更新文件列表，显示选中标记
        self._update_file_list()

    def _sort_files(self):
        """排序文件列表"""
        if self.sort_by == 'time_desc':
            # 按创建时间排序，最新的在前
            self.txt_files.sort(key=lambda x: self.file_info.get(x, {}).get('created_time', 0), reverse=True)
        elif self.sort_by == 'time_asc':
            # 按创建时间排序，最旧的在前
            self.txt_files.sort(key=lambda x: self.file_info.get(x, {}).get('created_time', 0))
        elif self.sort_by == 'name_asc':
            # 按文件名排序，A-Z
            self.txt_files.sort(key=lambda x: self.file_info.get(x, {}).get('name', ''))
        elif self.sort_by == 'name_desc':
            # 按文件名排序，Z-A
            self.txt_files.sort(key=lambda x: self.file_info.get(x, {}).get('name', ''), reverse=True)
        # 重置选中索引
        self.selected_index = -1

    def _on_content_change(self, e):
        """内容变化事件"""
        if self.selected_index >= 0 and self.selected_index < len(self.txt_files):
            file_path = self.txt_files[self.selected_index]
            self.file_contents[file_path] = e.value

    def _save_changes(self):
        """保存修改"""
        if self.selected_index >= 0 and self.selected_index < len(self.txt_files):
            file_path = self.txt_files[self.selected_index]
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.file_contents[file_path])
                ui.notify(self.t('file_saved'), type='positive')
            except Exception as e:
                ui.notify(self.t('save_failed').format(e), type='negative')
        else:
            ui.notify(self.t('select_first'), type='warning')

    def _delete_file(self):
        """删除文件"""
        if self.selected_index >= 0 and self.selected_index < len(self.txt_files):
            file_path = self.txt_files[self.selected_index]
            # 从列表中移除
            self.txt_files.pop(self.selected_index)
            self.file_contents.pop(file_path, None)
            self.file_info.pop(file_path, None)
            # 排序文件列表
            self._sort_files()
            # 更新文件列表
            self._update_file_list()
            # 清空预览
            self.ui_refs['editor'].value = ''
            self.selected_index = -1
            ui.notify(self.t('file_removed'), type='positive')
        else:
            ui.notify(self.t('select_first'), type='warning')

    def _clear_preview(self):
        """清空预览"""
        self.ui_refs['editor'].value = ''
        self.selected_index = -1

    def _on_sort_change(self, e):
        """排序方式变化事件"""
        # 根据当前语言判断排序方式
        sort_map = {
            'zh': {
                '按创建时间（最新在前）': 'time_desc',
                '按创建时间（最旧在前）': 'time_asc',
                '按文件名（A-Z）': 'name_asc',
                '按文件名（Z-A）': 'name_desc'
            },
            'en': {
                'By Time (Newest First)': 'time_desc',
                'By Time (Oldest First)': 'time_asc',
                'By Name (A-Z)': 'name_asc',
                'By Name (Z-A)': 'name_desc'
            }
        }
        self.sort_by = sort_map[self.current_lang].get(e.value, 'time_desc')
        # 排序文件列表
        self._sort_files()
        # 更新文件列表
        self._update_file_list()
        ui.notify(self.t('sorted_by').format(e.value), type='info')

    def _load_image_preview(self, file_path):
        """加载同名图片到图片预览区"""
        # 获取 TXT 文件的基础路径（不含扩展名）
        base_path = os.path.splitext(file_path)[0]
        
        # 检查是否存在同名的 jpg 或 png 文件
        image_extensions = ['.jpg', '.png']
        found_image = None
        
        for ext in image_extensions:
            image_path = base_path + ext
            if os.path.exists(image_path):
                found_image = image_path
                break
        
        if found_image:
            # 加载图片
            try:
                # 更新图片显示
                self.ui_refs['gallery'].set_source(found_image)
                self.ui_refs['gallery'].style('object-fit: contain;')
            except Exception as e:
                # 图片加载失败
                self.ui_refs['gallery'].set_source('')
                print(f"图片加载失败: {e}")
        else:
            # 无图片
            self.ui_refs['gallery'].set_source('')

    def _clear_file_list(self):
        """清空文件列表"""
        # 清空所有文件相关数据
        self.txt_files.clear()
        self.file_contents.clear()
        self.file_info.clear()
        self.selected_index = -1
        # 清空预览
        self.ui_refs['editor'].value = ''
        # 清空图片预览
        if 'gallery' in self.ui_refs:
            self.ui_refs['gallery'].set_source('')
        # 更新文件列表
        self._update_file_list()
        ui.notify(self.t('file_list_cleared'), type='positive')


@ui.page('/')
def main():
    """主页面"""
    # 创建 TXT 管理工具
    txt_manager = TxtManager()
    txt_manager.create()


def find_available_port(start_port=8080, max_port=8090):
    """查找可用端口"""
    import socket
    for port in range(start_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return None

if __name__ in {"__main__", "__mp_main__"}:
    import webbrowser
    import threading
    import time

    # 查找可用端口
    DEFAULT_PORT = 8080
    port = find_available_port(DEFAULT_PORT)

    if port is None:
        print(f'错误: 无法找到可用端口 (尝试范围 {DEFAULT_PORT}-8090)')
        exit(1)

    if port != DEFAULT_PORT:
        print(f'端口 {DEFAULT_PORT} 已被占用，自动切换到端口 {port}')

    def open_browser():
        time.sleep(2)
        webbrowser.open(f'http://localhost:{port}')
        print(f'已自动打开浏览器: http://localhost:{port}')

    threading.Thread(target=open_browser, daemon=True).start()

    print(f'启动 优可打标校验工具: http://localhost:{port}')
    ui.run(
        title='优可打标校验工具',
        host='127.0.0.1',
        port=port,
        reload=False,
        show=False
    )
