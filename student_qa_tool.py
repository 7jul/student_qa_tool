"""
学生手写问题智能问答工具
使用说明：
1. 按要求正确申请ocr-key与api-key，并填写在对应文件中
   - ocr.key 格式: 应用ID:应用密钥
   - api.key 格式: DeepSeek API密钥

2. 选择包含学生手写问题的图片文件
3. 文字识别后预览并确认问题
4. 选择学科老师智能体或让系统自动匹配
5. 获取专业解答和讲解
6. 可保存或打印问答记录
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
import requests
import base64
import time
import random
import string
import hashlib
from datetime import datetime

class StudentQATool:
    def __init__(self, root):
        self.root = root
        self.root.title("学生问题智能问答工具")
        self.root.geometry("1200x800")
        
        # 学科老师智能体定义
        self.teachers = {
            "数学老师": {
                "role": "数学老师",
                "prompt": "你是一位经验丰富的小学数学老师，擅长用简单生动的语言解释数学概念，通过生活中的例子帮助小学生理解数学问题。不需要在回答中复述学生的问题。"
            },
            "语文老师": {
                "role": "语文老师", 
                "prompt": "你是一位温和耐心的小学语文老师，擅长用通俗易懂的语言解释语文知识，通过有趣的故事和例子帮助小学生理解文字和语言。也能够帮助小学生修改和润色作文片段。不需要在回答中复述学生的问题。"
            },
            "英语老师": {
                "role": "英语老师",
                "prompt": "你是一位活泼开朗的小学英语老师，擅长用游戏和歌曲的方式教授英语，用简单的中文解释英语单词和句子。不需要在回答中复述学生的问题。"
            },
            "科学老师": {
                "role": "科学老师",
                "prompt": "你是一位充满好奇心的小学科学老师，擅长用实验和生活中的现象解释科学知识，让小学生感受科学的神奇和有趣。不需要在回答中复述学生的问题。"
            },
            "历史老师": {
                "role": "历史老师",
                "prompt": "你是一位博学有趣的小学历史老师，擅长用历史故事和人物传记让历史变得生动有趣，帮助小学生理解历史事件的意义。不需要在回答中复述学生的问题。"
            },
            "政治老师": {
                "role": "品德老师",
                "prompt": "你是一位和蔼可亲的小学品德老师，擅长用生活中的小故事和寓言讲道理，帮助小学生树立正确的价值观。不需要在回答中复述学生的问题。"
            }
            #"体育老师": {
            #    "role": "体育老师",
            #    "prompt": "你是一位阳光健康的小学体育老师，擅长用有趣的运动游戏和简单的身体训练帮助小学生了解运动知识，培养运动习惯，用生动的例子解释体育规则和健康知识。不需要在回答中复述学生的问题。"
            #}
        }
        
        # 问题关键词映射到学科
        self.subject_keywords = {
            "数学": ["数学", "计算", "加减", "乘除", "几何", "分数", "小数", "应用题", "算式", "数字"],
            "语文": ["语文", "作文", "阅读", "词语", "句子", "拼音", "汉字", "古诗", "课文", "造句"],
            "英语": ["英语", "单词", "字母", "句子", "对话", "语法", "翻译", "英文", "英语课"],
            "科学": ["科学", "实验", "自然", "植物", "动物", "天气", "物理", "化学", "生物", "地球"],
            "历史": ["历史", "古代", "现代", "朝代", "人物", "事件", "战争", "文化", "传统"],
            "政治": ["品德", "道德", "规则", "礼貌", "诚实", "友善", "爱国", "法律", "公民"],
            "体育老师": ["体育", "运动", "跑步", "跳远", "篮球", "足球", "跳绳", "游戏", "健康", "锻炼", "身体", "体能"]
        }
        
        self.setup_ui()
        self.current_qa = {}  # 保存当前问答记录
        
    def setup_ui(self):
        # 设置主窗口列权重，确保三个区域合理分配空间
        self.root.grid_columnconfigure(0, weight=3)   # OCR区域占较大比例
        self.root.grid_columnconfigure(1, weight=2)   # 老师选择区域占中等比例
        self.root.grid_columnconfigure(2, weight=1)   # 开始按钮区域占较小比例
        
        # OCR识别区域
        self.ocr_frame = tk.LabelFrame(self.root, text="手写问题识别", padx=10, pady=10)
        self.ocr_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # 图片选择
        tk.Button(self.ocr_frame, text="上传图片文字识别", 
                 command=self.select_image, font=("Microsoft YaHei", 12),
                 bg="#4CAF50", fg="white", padx=20, pady=10).grid(row=0, column=0, columnspan=2, pady=5)
        
        # OCR结果显示
        tk.Label(self.ocr_frame, text="识别出的问题:").grid(row=1, column=0, sticky="nw")
        self.ocr_text = tk.Text(self.ocr_frame, width=45, height=8)
        self.ocr_text.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        # 智能体选择区域 - 改为按钮组
        self.teacher_frame = tk.LabelFrame(self.root, text="选择老师", padx=10, pady=10)
        self.teacher_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        # 设置当前选择的老师
        self.selected_teacher = tk.StringVar(value="自动匹配")
        
        # 创建按钮网格
        self.create_teacher_buttons()
        
        # 开始问答按钮 - 移至右侧，独立区域
        self.start_frame = tk.Frame(self.root)
        self.start_frame.grid(row=0, column=2, padx=15, pady=15, sticky="nsew")
        
        # 设置框架的权重使其垂直居中
        self.start_frame.grid_rowconfigure(0, weight=1)
        self.start_frame.grid_rowconfigure(1, weight=0)  # 按钮行
        self.start_frame.grid_rowconfigure(2, weight=1)
        
        tk.Button(self.start_frame, text="开始问答", 
                 command=self.start_qa, font=("Microsoft YaHei", 14),
                 bg="#2196F3", fg="white", padx=30, pady=15, width=10, height=2).grid(row=1, column=0, padx=20)
        
        # 问答结果显示区域
        self.qa_frame = tk.LabelFrame(self.root, text="老师解答", padx=10, pady=10)
        self.qa_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=15, sticky="nsew")
        
        self.qa_text = tk.Text(self.qa_frame, width=80, height=20)
        self.qa_text.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # 操作按钮
        button_frame = tk.Frame(self.qa_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=5)
        
        tk.Button(button_frame, text="保存问答", command=self.save_qa).pack(side="left", padx=5)
        tk.Button(button_frame, text="加载问答", command=self.load_qa).pack(side="left", padx=5)
        tk.Button(button_frame, text="打印问答", command=self.print_qa).pack(side="left", padx=5)
        tk.Button(button_frame, text="清空", command=self.clear_all).pack(side="left", padx=5)
        
        # 配置网格权重
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=2)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        self.ocr_frame.grid_rowconfigure(2, weight=1)
        self.ocr_frame.grid_columnconfigure(0, weight=1)
        self.teacher_frame.grid_rowconfigure(2, weight=1)
        self.qa_frame.grid_rowconfigure(0, weight=1)
        self.qa_frame.grid_columnconfigure(0, weight=1)
        
        # 版权信息
        copyright_label = tk.Label(self.root, text="@天津市南开区南开小学-7jul", font=("Microsoft YaHei", 10))
        copyright_label.grid(row=2, column=0, columnspan=2, pady=5)
        
    def select_image(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.path.dirname(__file__),
            title="上传图片文字识别",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            self.image_path = file_path
            self.run_ocr()
            
    def run_ocr(self):
        if not hasattr(self, 'image_path'):
            messagebox.showerror("错误", "请先选择图片")
            return
            
        try:
            # 读取OCR密钥
            ocr_key_path = os.path.join(os.path.dirname(__file__), "..", "扫描识别并润色作文片段工作流", "ocr.key")
            with open(ocr_key_path, "r") as f:
                app_id, app_sec = f.read().strip().split(":")
        except Exception as e:
            messagebox.showerror("错误", f"读取ocr.key文件失败: {str(e)}")
            return
            
        try:
            # 读取图片并转换为base64
            with open(self.image_path, 'rb') as img_file:
                img_data = img_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # 调用OCR API
            param = {'img_base64': img_base64}
            result = self.get_ai_request(param, "general", "ocr_general", "v2", app_id, app_sec)
            
            # 解析结果
            result_data = json.loads(result)
            if 'result' in result_data and 'words_result' in result_data['result']:
                words_result = result_data['result']['words_result']
                if isinstance(words_result, list):
                    question_text = '\n'.join([item['words'] for item in words_result if 'words' in item])
                    self.ocr_text.delete(1.0, tk.END)
                    self.ocr_text.insert(tk.END, question_text)
                    
                    # 自动匹配学科
                    detected_subject = self.detect_subject(question_text)
                    if detected_subject:
                        self.select_teacher(detected_subject)
                        
        except Exception as e:
            messagebox.showerror("错误", f"OCR识别失败: {str(e)}")
            
    def create_teacher_buttons(self):
        """创建教师选择按钮"""
        # 自动匹配按钮
        self.auto_btn = tk.Button(self.teacher_frame, text="自动匹配学科", 
                                command=lambda: self.select_teacher("自动匹配"),
                                font=("Microsoft YaHei", 11), width=12, height=2,
                                bg="#FF9800", fg="white", relief=tk.RAISED)
        self.auto_btn.grid(row=0, column=0, padx=5, pady=5, columnspan=2)
        
        # 创建学科老师按钮
        teachers = list(self.teachers.keys())
        row = 1
        col = 0
        
        for i, teacher in enumerate(teachers):
            btn = tk.Button(self.teacher_frame, text=teacher,
                          command=lambda t=teacher: self.select_teacher(t),
                          font=("Microsoft YaHei", 11), width=12, height=2,
                          relief=tk.RAISED)
            btn.grid(row=row, column=col, padx=5, pady=5)
            
            # 设置不同颜色区分学科
            colors = {
                "数学老师": "#4CAF50",
                "语文老师": "#2196F3", 
                "英语老师": "#9C27B0",
                "科学老师": "#00BCD4",
                "历史老师": "#795548",
                "品德老师": "#E91E63",
                # "体育老师": "#FF5722"
            }
            btn.config(bg=colors.get(teacher, "#607D8B"), fg="white")
            
            # 更新行列位置
            col += 1
            if col > 1:  # 每行2个按钮
                col = 0
                row += 1
                
        # 设置默认选中的按钮样式
        self.update_button_styles()
        
    def select_teacher(self, teacher):
        """选择老师"""
        self.selected_teacher = teacher
        self.update_button_styles()
        
    def update_button_styles(self):
        """更新按钮样式以显示选中状态"""
        # 重置所有按钮样式
        for widget in self.teacher_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget['text'] != "开始问答":
                widget.config(relief=tk.RAISED)
                
        # 高亮选中的按钮
        for widget in self.teacher_frame.winfo_children():
            if isinstance(widget, tk.Button) and widget['text'] == self.selected_teacher:
                widget.config(relief=tk.SUNKEN, bd=3)
                
    def detect_subject(self, text):
        """根据问题内容自动检测学科"""
        text_lower = text.lower()
        for subject, keywords in self.subject_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    return f"{subject}老师"
        return "自动匹配"
        
    def get_ai_request(self, param, server, action, version, app_id, app_sec):
        """调用AI服务"""
        param = json.dumps(param)
        timestamp = str(round(time.time()*1000))
        salt = ''.join(random.sample(string.ascii_letters, 8))
        sign = app_id + app_sec + salt + timestamp
        sign = hashlib.md5(sign.encode(encoding='UTF-8')).hexdigest()
        
        headers = {
            'Content-Type': 'application/json',
            'app_id': app_id,
            'timestamp': timestamp,
            'salt': salt,
            'sign': sign
        }
        
        url = f"https://gate.ai.xdf.cn/{server}/{action}/{version}"
        response = requests.post(url, data=param, headers=headers)
        return response.text
        
    def start_qa(self):
        question = self.ocr_text.get(1.0, tk.END).strip()
        if not question:
            messagebox.showerror("错误", "请先识别出问题")
            return
            
        selected_teacher = self.selected_teacher
        
        try:
            # 读取API密钥
            api_key_path = os.path.join(os.path.dirname(__file__), "..", "扫描识别并润色作文片段工作流", "api.key")
            with open(api_key_path, "r") as f:
                api_key = f.read().strip()
        except Exception as e:
            messagebox.showerror("错误", f"读取api.key文件失败: {str(e)}")
            return
            
        try:
            # 获取智能体配置
            if selected_teacher == "自动匹配":
                detected_subject = self.detect_subject(question)
                if detected_subject and detected_subject in self.teachers:
                    teacher_config = self.teachers[detected_subject]
                else:
                    teacher_config = self.teachers["语文老师"]  # 默认语文老师
            else:
                teacher_config = self.teachers[selected_teacher]
                
            # 构建问答提示
            system_prompt = teacher_config["prompt"]
            user_prompt = f"""请回答以下小学生的问题，要求：
1. 用小学生能听懂的语言
2. 分析问题并给出清晰的解答
3. 字数控制在400字以内
4. 可以举简单的例子帮助理解

学生问题：{question}"""
            
            # 调用DeepSeek API
            response = self.call_deepseek_api(api_key, system_prompt, user_prompt)
            
            # 显示结果
            self.qa_text.delete(1.0, tk.END)
            qa_result = f"【{teacher_config['role']}回答】\n\n问题：{question}\n\n{response}"
            self.qa_text.insert(tk.END, qa_result)
            
            # 保存当前问答记录
            self.current_qa = {
                "question": question,
                "answer": response,
                "teacher": teacher_config["role"],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            messagebox.showerror("错误", f"问答失败: {str(e)}")
            
    def call_deepseek_api(self, api_key, system_prompt, user_prompt):
        """调用DeepSeek API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.8,
            "max_tokens": 600
        }
        
        response = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"API调用失败: {response.status_code} - {response.text}")
            
    def save_qa(self):
        if not self.current_qa:
            messagebox.showerror("错误", "没有可保存的问答记录")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialdir=os.path.dirname(__file__),
            title="保存问答记录"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.current_qa, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", "问答记录已保存")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
                
    def load_qa(self):
        file_path = filedialog.askopenfilename(
            initialdir=os.path.dirname(__file__),
            title="加载问答记录",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    qa_data = json.load(f)
                    
                self.current_qa = qa_data
                self.ocr_text.delete(1.0, tk.END)
                self.ocr_text.insert(tk.END, qa_data["question"])
                
                self.qa_text.delete(1.0, tk.END)
                qa_display = f"【{qa_data['teacher']}回答】\n\n问题：{qa_data['question']}\n\n{qa_data['answer']}\n\n记录时间：{qa_data['timestamp']}"
                self.qa_text.insert(tk.END, qa_display)
                
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {str(e)}")
                
    def print_qa(self):
        if not self.current_qa:
            messagebox.showerror("错误", "没有可打印的问答记录")
            return
            
        try:
            content = f"学生问题：{self.current_qa['question']}\n\n{self.current_qa['teacher']}回答：\n{self.current_qa['answer']}\n\n时间：{self.current_qa['timestamp']}"
            
            temp_file = os.path.join(os.path.dirname(__file__), "temp_qa_print.txt")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            os.startfile(temp_file, "print")
        except Exception as e:
            messagebox.showerror("错误", f"打印失败: {str(e)}")
            
    def clear_all(self):
        self.ocr_text.delete(1.0, tk.END)
        self.qa_text.delete(1.0, tk.END)
        self.current_qa = {}
        self.selected_teacher = "自动匹配"
        self.update_button_styles()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentQATool(root)
    root.mainloop()