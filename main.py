import sys
import os
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QFileDialog, QTextEdit, 
                            QTabWidget, QCheckBox, QLineEdit, QGroupBox, QRadioButton,
                            QProgressBar, QMessageBox, QSpinBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings

# Import file handlers
from file_handlers import (read_text_file, read_pdf_file, read_docx_file, 
                          read_epub_file, read_srt_file, write_text_file, 
                          write_srt_file, merge_subtitles)

# Import model handlers
from model_handlers import (detect_ollama_models, translate_with_ollama,
                           translate_with_api)

# 定义语言字典
TRANSLATIONS = {
    "en": {
        "app_title": "Long Text Translator",
        "translation_tab": "Translation",
        "settings_tab": "Settings",
        "file_selection": "File Selection",
        "input_file": "Input File:",
        "output_file": "Output File:",
        "browse": "Browse...",
        "file_type": "File Type:",
        "subtitle_options": "Subtitle Options",
        "merge_bilingual": "Merge bilingual subtitles",
        "translation_options": "Translation Options",
        "model_type": "Model Type:",
        "ollama_local": "Ollama (Local)",
        "api_online": "API (Online)",
        "ollama_options": "Ollama Options",
        "model": "Model:",
        "refresh": "Refresh",
        "api_options": "API Options",
        "api_url": "API URL:",
        "api_key": "API Key:",
        "language_options": "Language Options",
        "source_language": "Source Language:",
        "target_language": "Target Language:",
        "progress": "Progress:",
        "log": "Log:",
        "translate": "Translate",
        "ollama_settings": "Ollama Settings",
        "ollama_host": "Ollama Host:",
        "save_settings": "Save Settings",
        "app_language": "Application Language:",
        "app_initialized": "Application initialized",
        "refreshing_models": "Refreshing Ollama models...",
        "found_models": "Found {} Ollama models",
        "error_refreshing": "Error refreshing Ollama models: {}",
        "settings_saved": "Settings saved",
        "warning": "Warning",
        "select_input": "Please select an input file",
        "select_output": "Please select an output file",
        "no_models": "No Ollama models available",
        "enter_api_url": "Please enter API URL",
        "starting_translation": "Starting translation of {}...",
        "success": "Success",
        "error": "Error",
        "translation_completed": "Translation completed: {}"
    },
    "zh": {
        "app_title": "长文本翻译器",
        "translation_tab": "翻译",
        "settings_tab": "设置",
        "file_selection": "文件选择",
        "input_file": "输入文件：",
        "output_file": "输出文件：",
        "browse": "浏览...",
        "file_type": "文件类型：",
        "subtitle_options": "字幕选项",
        "merge_bilingual": "合并双语字幕",
        "translation_options": "翻译选项",
        "model_type": "模型类型：",
        "ollama_local": "Ollama (本地)",
        "api_online": "API (在线)",
        "ollama_options": "Ollama 选项",
        "model": "模型：",
        "refresh": "刷新",
        "api_options": "API 选项",
        "api_url": "API 地址：",
        "api_key": "API 密钥：",
        "language_options": "语言选项",
        "source_language": "源语言：",
        "target_language": "目标语言：",
        "progress": "进度：",
        "log": "日志：",
        "translate": "翻译",
        "ollama_settings": "Ollama 设置",
        "ollama_host": "Ollama 主机：",
        "save_settings": "保存设置",
        "app_language": "应用程序语言：",
        "app_initialized": "应用程序已初始化",
        "refreshing_models": "正在刷新 Ollama 模型...",
        "found_models": "找到 {} 个 Ollama 模型",
        "error_refreshing": "刷新 Ollama 模型出错：{}",
        "settings_saved": "设置已保存",
        "warning": "警告",
        "select_input": "请选择输入文件",
        "select_output": "请选择输出文件",
        "no_models": "没有可用的 Ollama 模型",
        "enter_api_url": "请输入 API 地址",
        "starting_translation": "开始翻译 {}...",
        "success": "成功",
        "error": "错误",
        "translation_completed": "翻译完成：{}"
    }
}

class TranslationThread(QThread):
    progress_signal = pyqtSignal(int)
    result_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, input_file, output_file, file_type, model_type, model_name, 
                 api_url=None, api_key=None, merge_bilingual=False, source_lang="auto", target_lang="en"):
        super().__init__()
        self.input_file = input_file
        self.output_file = output_file
        self.file_type = file_type
        self.model_type = model_type
        self.model_name = model_name
        self.api_url = api_url
        self.api_key = api_key
        self.merge_bilingual = merge_bilingual
        self.source_lang = source_lang
        self.target_lang = target_lang
        
    def run(self):
        try:
            # Read the input file
            content = None
            if self.file_type == "txt":
                content = read_text_file(self.input_file)
            elif self.file_type == "pdf":
                content = read_pdf_file(self.input_file)
            elif self.file_type == "docx":
                content = read_docx_file(self.input_file)
            elif self.file_type == "epub":
                content = read_epub_file(self.input_file)
            elif self.file_type == "srt":
                content = read_srt_file(self.input_file)
            
            if content is None:
                self.error_signal.emit(f"Failed to read {self.input_file}")
                return
            
            # Translate the content
            translated_content = None
            if self.model_type == "ollama":
                translated_content = translate_with_ollama(
                    content, 
                    self.model_name, 
                    self.source_lang, 
                    self.target_lang,
                    self.progress_signal
                )
            elif self.model_type == "api":
                translated_content = translate_with_api(
                    content, 
                    self.api_url, 
                    self.api_key, 
                    self.source_lang, 
                    self.target_lang,
                    self.progress_signal
                )
            
            if translated_content is None:
                self.error_signal.emit("Translation failed")
                return
            
            # Write the output file
            if self.file_type == "srt" and self.merge_bilingual:
                merged_content = merge_subtitles(content, translated_content)
                write_srt_file(self.output_file, merged_content)
            elif self.file_type == "srt":
                write_srt_file(self.output_file, translated_content)
            else:
                write_text_file(self.output_file, translated_content)
            
            self.result_signal.emit(self.output_file)
            
        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("LongTextTranslator", "Settings")
        
        # 获取界面语言设置，默认为英文
        self.current_language = self.settings.value("language", "en")
        
        # 设置窗口标题
        self.setWindowTitle(self.tr("app_title"))
        self.setMinimumSize(800, 600)
        
        # 主窗口部件和布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 翻译标签页
        translation_tab = QWidget()
        translation_layout = QVBoxLayout()
        translation_tab.setLayout(translation_layout)
        self.tabs.addTab(translation_tab, self.tr("translation_tab"))
        
        # 设置标签页
        settings_tab = QWidget()
        settings_layout = QVBoxLayout()
        settings_tab.setLayout(settings_layout)
        self.tabs.addTab(settings_tab, self.tr("settings_tab"))
        
        # 文件选择组
        self.file_group = QGroupBox(self.tr("file_selection"))
        file_layout = QVBoxLayout()
        self.file_group.setLayout(file_layout)
        translation_layout.addWidget(self.file_group)
        
        # 输入文件
        input_layout = QHBoxLayout()
        self.input_label = QLabel(self.tr("input_file"))
        self.input_path = QLineEdit()
        self.input_path.setReadOnly(True)
        self.input_button = QPushButton(self.tr("browse"))
        self.input_button.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(self.input_button)
        file_layout.addLayout(input_layout)
        
        # 输出文件
        output_layout = QHBoxLayout()
        self.output_label = QLabel(self.tr("output_file"))
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        self.output_button = QPushButton(self.tr("browse"))
        self.output_button.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(self.output_button)
        file_layout.addLayout(output_layout)
        
        # 文件类型检测
        file_type_layout = QHBoxLayout()
        self.file_type_label = QLabel(self.tr("file_type"))
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["txt", "pdf", "docx", "epub", "srt"])
        file_type_layout.addWidget(self.file_type_label)
        file_type_layout.addWidget(self.file_type_combo)
        file_layout.addLayout(file_type_layout)
        
        # 字幕选项（仅适用于SRT）
        self.subtitle_options = QGroupBox(self.tr("subtitle_options"))
        subtitle_layout = QVBoxLayout()
        self.subtitle_options.setLayout(subtitle_layout)
        self.merge_bilingual = QCheckBox(self.tr("merge_bilingual"))
        subtitle_layout.addWidget(self.merge_bilingual)
        file_layout.addWidget(self.subtitle_options)
        self.subtitle_options.setVisible(False)
        
        # 连接文件类型更改到字幕选项可见性
        self.file_type_combo.currentTextChanged.connect(self.update_subtitle_options)
        
        # 翻译选项组
        self.translation_group = QGroupBox(self.tr("translation_options"))
        translation_options_layout = QVBoxLayout()
        self.translation_group.setLayout(translation_options_layout)
        translation_layout.addWidget(self.translation_group)
        
        # 模型选择
        model_layout = QHBoxLayout()
        self.model_type_label = QLabel(self.tr("model_type"))
        self.model_type = QComboBox()
        self.model_type.addItems([self.tr("ollama_local"), self.tr("api_online")])
        self.model_type.currentTextChanged.connect(self.update_model_options)
        model_layout.addWidget(self.model_type_label)
        model_layout.addWidget(self.model_type)
        translation_options_layout.addLayout(model_layout)
        
        # Ollama模型选项
        self.ollama_group = QGroupBox(self.tr("ollama_options"))
        ollama_layout = QVBoxLayout()
        self.ollama_group.setLayout(ollama_layout)
        
        # Ollama模型选择
        ollama_model_layout = QHBoxLayout()
        self.ollama_model_label = QLabel(self.tr("model"))
        self.ollama_model_combo = QComboBox()
        self.refresh_button = QPushButton(self.tr("refresh"))
        self.refresh_button.clicked.connect(self.refresh_ollama_models)
        ollama_model_layout.addWidget(self.ollama_model_label)
        ollama_model_layout.addWidget(self.ollama_model_combo)
        ollama_model_layout.addWidget(self.refresh_button)
        ollama_layout.addLayout(ollama_model_layout)
        
        translation_options_layout.addWidget(self.ollama_group)
        
        # API选项
        self.api_group = QGroupBox(self.tr("api_options"))
        api_layout = QVBoxLayout()
        self.api_group.setLayout(api_layout)
        
        # API URL
        api_url_layout = QHBoxLayout()
        self.api_url_label = QLabel(self.tr("api_url"))
        self.api_url = QLineEdit()
        self.api_url.setText(self.settings.value("api_url", ""))
        api_url_layout.addWidget(self.api_url_label)
        api_url_layout.addWidget(self.api_url)
        api_layout.addLayout(api_url_layout)
        
        # API Key
        api_key_layout = QHBoxLayout()
        self.api_key_label = QLabel(self.tr("api_key"))
        self.api_key = QLineEdit()
        self.api_key.setText(self.settings.value("api_key", ""))
        api_key_layout.addWidget(self.api_key_label)
        api_key_layout.addWidget(self.api_key)
        api_layout.addLayout(api_key_layout)
        
        translation_options_layout.addWidget(self.api_group)
        
        # 语言选项
        self.lang_group = QGroupBox(self.tr("language_options"))
        lang_layout = QVBoxLayout()
        self.lang_group.setLayout(lang_layout)
        
        # 源语言
        source_layout = QHBoxLayout()
        self.source_label = QLabel(self.tr("source_language"))
        self.source_lang = QComboBox()
        self.source_lang.addItems(["auto", "en", "zh", "ja", "ko", "fr", "de", "es", "ru"])
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_lang)
        lang_layout.addLayout(source_layout)
        
        # 目标语言
        target_layout = QHBoxLayout()
        self.target_label = QLabel(self.tr("target_language"))
        self.target_lang = QComboBox()
        self.target_lang.addItems(["en", "zh", "ja", "ko", "fr", "de", "es", "ru"])
        target_layout.addWidget(self.target_label)
        target_layout.addWidget(self.target_lang)
        lang_layout.addLayout(target_layout)
        
        translation_options_layout.addWidget(self.lang_group)
        
        # 进度条
        progress_layout = QVBoxLayout()
        self.progress_label = QLabel(self.tr("progress"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        translation_layout.addLayout(progress_layout)
        
        # 状态和日志
        self.log_label = QLabel(self.tr("log"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        translation_layout.addWidget(self.log_label)
        translation_layout.addWidget(self.log_text)
        
        # 翻译按钮
        self.translate_button = QPushButton(self.tr("translate"))
        self.translate_button.clicked.connect(self.start_translation)
        translation_layout.addWidget(self.translate_button)
        
        # 设置标签页内容
        # Ollama设置
        self.ollama_settings_group = QGroupBox(self.tr("ollama_settings"))
        ollama_settings_layout = QVBoxLayout()
        self.ollama_settings_group.setLayout(ollama_settings_layout)
        
        # Ollama主机
        ollama_host_layout = QHBoxLayout()
        self.ollama_host_label = QLabel(self.tr("ollama_host"))
        self.ollama_host = QLineEdit()
        self.ollama_host.setText(self.settings.value("ollama_host", "http://localhost:11434"))
        ollama_host_layout.addWidget(self.ollama_host_label)
        ollama_host_layout.addWidget(self.ollama_host)
        ollama_settings_layout.addLayout(ollama_host_layout)
        
        # 应用程序语言选择
        app_lang_layout = QHBoxLayout()
        self.app_lang_label = QLabel(self.tr("app_language"))
        self.app_lang_combo = QComboBox()
        self.app_lang_combo.addItems(["English", "中文"])
        # 设置当前语言
        if self.current_language == "zh":
            self.app_lang_combo.setCurrentIndex(1)
        else:
            self.app_lang_combo.setCurrentIndex(0)
        app_lang_layout.addWidget(self.app_lang_label)
        app_lang_layout.addWidget(self.app_lang_combo)
        ollama_settings_layout.addLayout(app_lang_layout)
        
        # 保存设置按钮
        self.save_settings_button = QPushButton(self.tr("save_settings"))
        self.save_settings_button.clicked.connect(self.save_settings)
        ollama_settings_layout.addWidget(self.save_settings_button)
        
        settings_layout.addWidget(self.ollama_settings_group)
        
        # 初始化UI状态
        self.update_model_options()
        self.refresh_ollama_models()
        
        # 日志初始化
        self.log(self.tr("app_initialized"))
    
    def tr(self, key):
        """翻译函数，根据当前语言返回对应的文本"""
        return TRANSLATIONS[self.current_language].get(key, key)
    
    def update_subtitle_options(self):
        file_type = self.file_type_combo.currentText()
        self.subtitle_options.setVisible(file_type == "srt")
    
    def update_model_options(self):
        model_type = self.model_type.currentText()
        if self.tr("ollama_local") in model_type:
            self.ollama_group.setVisible(True)
            self.api_group.setVisible(False)
        else:
            self.ollama_group.setVisible(False)
            self.api_group.setVisible(True)
    
    def refresh_ollama_models(self):
        self.log(self.tr("refreshing_models"))
        try:
            ollama_host = self.ollama_host.text()
            models = detect_ollama_models(ollama_host)
            self.ollama_model_combo.clear()
            self.ollama_model_combo.addItems(models)
            self.log(self.tr("found_models").format(len(models)))
        except Exception as e:
            self.log(self.tr("error_refreshing").format(str(e)))
    
    def select_input_file(self):
        file_type = self.file_type_combo.currentText()
        file_filter = ""
        if file_type == "txt":
            file_filter = "Text files (*.txt)"
        elif file_type == "pdf":
            file_filter = "PDF files (*.pdf)"
        elif file_type == "docx":
            file_filter = "Word files (*.docx)"
        elif file_type == "epub":
            file_filter = "EPUB files (*.epub)"
        elif file_type == "srt":
            file_filter = "Subtitle files (*.srt)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", file_filter
        )
        
        if file_path:
            self.input_path.setText(file_path)
            # 自动生成输出路径
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            output_path = os.path.join(
                os.path.dirname(file_path),
                f"{name}_translated{ext}"
            )
            self.output_path.setText(output_path)
    
    def select_output_file(self):
        file_type = self.file_type_combo.currentText()
        file_filter = ""
        if file_type == "txt":
            file_filter = "Text files (*.txt)"
        elif file_type == "pdf":
            file_filter = "Text files (*.txt)"  # PDF输出为文本
        elif file_type == "docx":
            file_filter = "Text files (*.txt)"  # DOCX输出为文本
        elif file_type == "epub":
            file_filter = "Text files (*.txt)"  # EPUB输出为文本
        elif file_type == "srt":
            file_filter = "Subtitle files (*.srt)"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File", "", file_filter
        )
        
        if file_path:
            self.output_path.setText(file_path)
    
    def save_settings(self):
        self.settings.setValue("ollama_host", self.ollama_host.text())
        self.settings.setValue("api_url", self.api_url.text())
        self.settings.setValue("api_key", self.api_key.text())
        
        # 保存语言设置
        lang_index = self.app_lang_combo.currentIndex()
        if lang_index == 1:  # 中文
            self.settings.setValue("language", "zh")
            self.current_language = "zh"
        else:  # 英文
            self.settings.setValue("language", "en")
            self.current_language = "en"
        
        self.log(self.tr("settings_saved"))
        
        # 提示用户需要重启应用程序以应用语言更改
        QMessageBox.information(self, "Info", "Language settings saved. Please restart the application to apply changes.")
    
    def log(self, message):
        self.log_text.append(message)
    
    def start_translation(self):
        # 验证输入
        input_file = self.input_path.text()
        output_file = self.output_path.text()
        file_type = self.file_type_combo.currentText()
        
        if not input_file:
            QMessageBox.warning(self, self.tr("warning"), self.tr("select_input"))
            return
        
        if not output_file:
            QMessageBox.warning(self, self.tr("warning"), self.tr("select_output"))
            return
        
        # 获取模型设置
        model_type = "ollama" if self.tr("ollama_local") in self.model_type.currentText() else "api"
        
        if model_type == "ollama":
            if self.ollama_model_combo.count() == 0:
                QMessageBox.warning(self, self.tr("warning"), self.tr("no_models"))
                return
            model_name = self.ollama_model_combo.currentText()
            api_url = None
            api_key = None
        else:
            model_name = None
            api_url = self.api_url.text()
            api_key = self.api_key.text()
            
            if not api_url:
                QMessageBox.warning(self, self.tr("warning"), self.tr("enter_api_url"))
                return
        
        # 获取语言设置
        source_lang = self.source_lang.currentText()
        target_lang = self.target_lang.currentText()
        
        # 获取字幕选项
        merge_bilingual = False
        if file_type == "srt":
            merge_bilingual = self.merge_bilingual.isChecked()
        
        # 在翻译期间禁用UI
        self.translate_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # 创建并启动翻译线程
        self.translation_thread = TranslationThread(
            input_file, output_file, file_type, model_type, model_name,
            api_url, api_key, merge_bilingual, source_lang, target_lang
        )
        
        self.translation_thread.progress_signal.connect(self.update_progress)
        self.translation_thread.result_signal.connect(self.translation_completed)
        self.translation_thread.error_signal.connect(self.translation_error)
        
        self.log(self.tr("starting_translation").format(input_file))
        self.translation_thread.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def translation_completed(self, output_file):
        message = self.tr("translation_completed").format(output_file)
        self.log(message)
        self.translate_button.setEnabled(True)
        QMessageBox.information(self, self.tr("success"), message)
    
    def translation_error(self, error_message):
        self.log(f"{self.tr('error')}: {error_message}")
        self.translate_button.setEnabled(True)
        QMessageBox.critical(self, self.tr("error"), error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
