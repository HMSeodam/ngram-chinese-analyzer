import tkinter as tk
from tkinter import filedialog, messagebox
import re, os, threading, time, html, random, colorsys
from collections import Counter

# 워드클라우드 및 matplotlib 관련 모듈
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- 한자 획수 계산 함수 ---  
def get_stroke_count(ch):
    if ch == '一':
        return 1
    if ch == '二':
        return 2
    return ord(ch) % 20 + 1

# --- 워드클라우드에 사용할 다양한 색상 함수 (HSL 기반, 노란색 계열 제외) ---
def diverse_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    if random_state is None:
        random_state = random.Random()
    while True:
        hue = random_state.uniform(0, 360)
        if not (50 <= hue <= 70):
            break
    h = hue / 360.0
    s = random_state.uniform(0.7, 1.0)  # 채도: 70~100%
    l = random_state.uniform(0.3, 0.7)  # 밝기: 30~70%
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    r, g, b = int(r*255), int(g*255), int(b*255)
    return f"#{r:02x}{g:02x}{b:02x}"

class NgramAnalyzer:
    def __init__(self, master):
        self.master = master
        master.title("N-gram-Based Program for Comparing Chinese Texts")
        
        # 내부 데이터 저장 변수들
        self.files_data = {}           # 파일명 -> 한자만 남긴 텍스트 (처리된 텍스트)
        self.index_map = {}            # 파일명 -> 원본 텍스트에서 한자 위치(인덱스) 리스트
        self.original_text_data = {}   # 파일명 -> 원본 전체 텍스트
        self.ngram_results = {}        # 파일명 -> n-gram 카운터
        self.all_ngrams = set()        # 전체 n-gram 집합
        self.filtered_mode = "common"  # 모드는 오직 "공통 부분"만 사용
        self.filtered_files = []       # 필터링 시 선택된 파일명들
        self.original_result_text = "" # 전체 분석 결과 텍스트 저장
        self.apply_selection_window = None  # 비교 결과 적용할 파일 선택 창
        
        self.cancel_requested = False  # 진행중인 작업 취소 여부 플래그

        # 상단: N‑gram 최소, 최대 값 입력 영역
        top_frame = tk.Frame(master)
        top_frame.pack(padx=10, pady=5, anchor="center")
        tk.Label(top_frame, text="N-gram 최소 값(2부터 시작):").grid(row=0, column=0, padx=5)
        self.min_entry = tk.Entry(top_frame, width=5)
        self.min_entry.insert(0, "2")
        self.min_entry.grid(row=0, column=1, padx=5)
        tk.Label(top_frame, text="N-gram 최대 값(예: 4):").grid(row=0, column=2, padx=5)
        self.max_entry = tk.Entry(top_frame, width=5)
        self.max_entry.insert(0, "4")
        self.max_entry.grid(row=0, column=3, padx=5)
        
        # 액션 버튼 영역: 파일 비교, 모드(공통 부분 선택), 비교 결과 적용하기
        action_frame = tk.Frame(master)
        action_frame.pack(padx=10, pady=5)
        self.compare_button = tk.Button(action_frame, text="파일 비교", command=self.compare_files, width=15)
        self.compare_button.grid(row=0, column=0, padx=5)
        
        # 모드 버튼: "공통 부분" (오른쪽에 "▼" 아이콘)
        self.mode_value = tk.StringVar(value="공통 부분")
        self.mode_container = tk.Frame(action_frame, bd=1, relief="sunken")
        mode_label = tk.Label(self.mode_container, textvariable=self.mode_value, width=10, anchor="center")
        mode_label.pack(side=tk.LEFT, padx=2, pady=2)
        mode_button = tk.Button(self.mode_container, text="▼", command=lambda: self.set_mode("common"), width=2)
        mode_button.pack(side=tk.RIGHT, padx=2, pady=2)
        self.mode_container.grid(row=0, column=1, padx=10)
        
        self.apply_button = tk.Button(action_frame, text="비교 결과 적용하기", command=self.apply_comparison, width=15)
        self.apply_button.grid(row=0, column=2, padx=5)
        
        # 대기 팝업 변수
        self.popup = None
        
        # 필터 버튼 영역 (공통 부분 선택 등, 여기에서 정렬 기준 드롭다운이 생성됨)
        default_bg = master.cget("bg")
        self.filter_button_frame = tk.Frame(master, bg=default_bg)
        self.filter_button_frame.pack(padx=10, pady=5, fill=tk.X)
        
        # 데이터 항목 수 표시 라벨
        self.data_count_label = tk.Label(master, text="데이터 항목 수: 0개")
        self.data_count_label.pack(padx=10, pady=(5,0))
        
        # 중앙: n-gram 분석 결과를 보여주는 텍스트 영역
        result_frame = tk.Frame(master)
        result_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        self.result_text = tk.Text(result_frame, wrap=tk.NONE)
        self.result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scrollbar = tk.Scrollbar(result_frame, command=self.result_text.yview)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_text.config(yscrollcommand=y_scrollbar.set)
        
        # 하단: 저장 및 워드클라우드 버튼 – 가운데 정렬
        bottom_frame = tk.Frame(master)
        bottom_frame.pack(padx=10, pady=5)
        self.save_button = tk.Button(bottom_frame, text="N-gram 분석 결과 저장하기", command=self.save_ngram_results)
        self.save_button.pack(side=tk.LEFT, padx=5)
        self.wordcloud_button = tk.Button(bottom_frame, text="워드클라우드", command=self.show_wordcloud)
        self.wordcloud_button.pack(side=tk.LEFT, padx=5)
        
        # 정렬 기준 드롭다운은 처음엔 보이지 않음 (공통 부분 선택 시 생성)
        self.sort_frame = None

    # --- 정렬 기준 드롭다운 생성 (공통 부분 버튼 클릭 시 생성됨) ---
    def create_sort_widget(self):
        if self.sort_frame is not None:
            return
        self.sort_frame = tk.Frame(self.filter_button_frame)
        self.sort_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(self.sort_frame, text="정렬 기준:").pack(side=tk.LEFT)
        # 이제 정렬 옵션은 빈도수 관련 옵션만 제공됩니다.
        self.sort_selection = tk.StringVar(value="빈도수 오름차순")
        self.sort_menubutton = tk.Menubutton(self.sort_frame, text=self.sort_selection.get() + " ▼", relief="raised")
        self.sort_menu = tk.Menu(self.sort_menubutton, tearoff=0)
        options = ["빈도수 오름차순", "빈도수 내림차순"]
        for option in options:
            self.sort_menu.add_command(label=option, command=lambda opt=option: self.set_sort_option(opt))
        self.sort_menubutton.config(menu=self.sort_menu)
        self.sort_menubutton.pack(side=tk.LEFT, padx=5)
    
    def set_sort_option(self, option):
        self.sort_selection.set(option)
        self.sort_menubutton.config(text=option + " ▼")
        self.apply_filter()
    
    def get_current_sort_option(self):
        return self.sort_selection.get() if self.sort_frame is not None else None

    # --- n-gram 정렬 (빈도수 기준으로 정렬) ---
    def sort_ngrams(self, ngrams, file_set):
        option = self.get_current_sort_option()
        if option is None:
            option = "빈도수 오름차순"
        if option in ["빈도수 오름차순", "빈도수 내림차순"]:
            def freq_key(ngram):
                return sum(self.ngram_results[fname].get(ngram, 0) for fname in file_set)
            reverse = (option == "빈도수 내림차순")
            return sorted(ngrams, key=freq_key, reverse=reverse)
        else:
            def freq_key(ngram):
                return sum(self.ngram_results[fname].get(ngram, 0) for fname in file_set)
            return sorted(ngrams, key=freq_key)
    
    # --- 로딩 팝업 ---
    def show_waiting_popup(self, message=None):
        if message is None:
            message = "작업량에 따라 몇 분 정도 걸릴 수 있습니다. 잠시만 기다려 주세요."
        if self.popup is None:
            self.cancel_requested = False
            self.popup = tk.Toplevel(self.master)
            self.popup.title("로딩중입니다..")
            tk.Label(self.popup, text=message).pack(padx=20, pady=20)
            tk.Button(self.popup, text="취소", command=self.cancel_operation).pack(pady=10)
            self.popup.geometry("400x150")
            self.master.attributes("-disabled", True)
            self.popup.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def cancel_operation(self):
        self.cancel_requested = True
        self.close_waiting_popup()
    
    def close_waiting_popup(self):
        if self.popup is not None:
            self.master.attributes("-disabled", False)
            self.popup.destroy()
            self.popup = None
    
    def update_data_count(self, text):
        count = len([line for line in text.splitlines() if line.strip()])
        self.data_count_label.config(text=f"데이터 항목 수: {count}개")
    
    # --- 파일 비교 및 n-gram 처리 ---
    def compare_files(self):
        file_paths = filedialog.askopenfilenames(
            title="비교할 파일 선택",
            filetypes=[("Text files", "*.txt"), ("HWP files", "*.hwp"),
                       ("HTML files", "*.html"), ("All files", "*.*")]
        )
        if not file_paths or len(file_paths) < 2:
            messagebox.showerror("에러", "최소 2개 이상의 파일을 선택해야 합니다.")
            return
        self.cancel_requested = False
        thread = threading.Thread(target=self.process_files, args=(file_paths,))
        thread.start()
        self.master.after(2500, lambda: self.show_waiting_popup() if thread.is_alive() and not self.cancel_requested else None)
    
    def process_files(self, file_paths):
        self.files_data.clear()
        self.index_map.clear()
        self.original_text_data.clear()
        self.ngram_results.clear()
        self.all_ngrams.clear()
        self.original_result_text = ""
        try:
            min_n = int(self.min_entry.get())
            max_n = int(self.max_entry.get())
        except ValueError:
            messagebox.showerror("에러", "N-gram 최소 값과 최대 값은 숫자로 입력해야 합니다.")
            return
        hanja_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4DBF\uF900-\uFAFF\U00020000-\U0002A6DF]')
        for path in file_paths:
            if self.cancel_requested:
                self.master.after(0, self.close_waiting_popup)
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                messagebox.showerror("파일 에러", f"{os.path.basename(path)} 파일 읽는 중 오류 발생: {str(e)}")
                continue
            file_name = os.path.splitext(os.path.basename(path))[0]
            self.original_text_data[file_name] = content
            processed_text = ""
            index_mapping = []
            for i, ch in enumerate(content):
                if hanja_pattern.match(ch):
                    processed_text += ch
                    index_mapping.append(i)
            self.files_data[file_name] = processed_text
            self.index_map[file_name] = index_mapping
            counter = Counter()
            text_len = len(processed_text)
            for n in range(min_n, max_n+1):
                for i in range(text_len - n + 1):
                    if self.cancel_requested:
                        return
                    ngram = processed_text[i:i+n]
                    counter[ngram] += 1
            self.ngram_results[file_name] = counter
            self.all_ngrams.update(counter.keys())
        # n-gram 정렬 (현재 정렬 기준에 따라)
        file_keys = list(self.ngram_results.keys())
        sorted_ngrams = self.sort_ngrams(self.all_ngrams, file_keys)
        lines = []
        for ngram in sorted_ngrams:
            parts = []
            for fname, counter in self.ngram_results.items():
                count = counter.get(ngram, 0)
                parts.append(f"{fname}: {count}")
            lines.append(f"{ngram}: " + ", ".join(parts))
        self.original_result_text = "\n".join(lines)
        self.master.after(0, lambda: self.result_text.delete("1.0", tk.END))
        self.master.after(0, lambda: self.result_text.insert(tk.END, self.original_result_text))
        self.master.after(0, self.update_data_count, self.original_result_text)
        self.master.after(0, self.clear_filter_buttons)
        self.master.after(0, self.close_waiting_popup)
    
    def clear_filter_buttons(self):
        for widget in self.filter_button_frame.winfo_children():
            widget.destroy()
    
    # --- '공통 부분' 선택 (모드 전환 시 정렬 드롭다운 생성) ---
    def set_mode(self, mode):
        self.filtered_mode = "common"
        self.mode_value.set("공통 부분")
        self.clear_filter_buttons()
        default_bg = self.master.cget("bg")
        subframe = tk.Frame(self.filter_button_frame, bg=default_bg)
        subframe.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(subframe, text="공통 부분 선택:", bg=default_bg).grid(row=0, column=0, padx=5, sticky="w")
        self.common_selection = {}
        col = 1
        for fname in self.files_data.keys():
            var = tk.BooleanVar()
            chk = tk.Checkbutton(subframe, text=fname, variable=var, command=self.update_common_filter, bg=default_bg)
            chk.grid(row=0, column=col, padx=2)
            self.common_selection[fname] = var
            col += 1
        self.include_all_common = tk.BooleanVar(value=False)
        # 수정: 파일이 2개 선택되어도 '모든 교집합 포함' 체크박스가 활성화되도록 state를 항상 tk.NORMAL으로 설정
        state = tk.NORMAL
        chk_all_common = tk.Checkbutton(subframe, text="모든 교집합 포함", variable=self.include_all_common,
                                        command=self.update_common_filter, bg=default_bg, state=state)
        chk_all_common.grid(row=1, column=0, columnspan=col, padx=5, pady=5, sticky="w")
        # 여기서 정렬 기준 드롭다운(빈도수 관련 옵션만 포함)도 생성됨
        self.create_sort_widget()
        self.apply_filter()
    
    def update_common_filter(self):
        selected = [fname for fname, var in self.common_selection.items() if var.get()]
        self.filtered_files = selected
        self.apply_filter()
    
    def apply_filter(self):
        filtered_lines = []
        sort_base = self.filtered_files if self.filtered_mode == "common" else list(self.ngram_results.keys())
        for ngram in self.sort_ngrams(self.all_ngrams, sort_base):
            if self.filtered_mode == "common":
                if self.include_all_common.get():
                    if self.filtered_files and all(self.ngram_results[fname].get(ngram, 0) > 0 for fname in self.filtered_files):
                        parts = [f"{fname}: {self.ngram_results[fname].get(ngram,0)}" for fname in self.filtered_files]
                        filtered_lines.append(f"{ngram}: " + ", ".join(parts))
                else:
                    selected_set = set(self.filtered_files)
                    appearance_set = {fname for fname, counter in self.ngram_results.items() if counter.get(ngram, 0) > 0}
                    if appearance_set == selected_set and appearance_set:
                        parts = [f"{fname}: {self.ngram_results[fname].get(ngram,0)}" for fname in self.filtered_files]
                        filtered_lines.append(f"{ngram}: " + ", ".join(parts))
            else:
                filtered_lines = self.original_result_text.split("\n")
                break
        filtered_text = "\n".join(filtered_lines)
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, filtered_text)
        self.update_data_count(filtered_text)
    
    def save_ngram_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt"), ("HTML files", "*.html"), ("HWP files", "*.hwp")])
        if file_path:
            content = self.result_text.get("1.0", tk.END)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("저장 완료", f"분석 결과가 {os.path.basename(file_path)}에 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("저장 에러", f"파일 저장 중 오류 발생: {str(e)}")
    
    # --- 워드클라우드 창 생성 ---
    def show_wordcloud(self):
        visible_text = self.result_text.get("1.0", tk.END)
        if not visible_text.strip():
            messagebox.showerror("에러", "워드클라우드를 생성할 데이터가 없습니다.")
            return
        freq_dict = {}
        for line in visible_text.splitlines():
            if line.strip():
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                ngram = parts[0].strip()
                counts = re.findall(r'\d+', line)
                total = sum(int(x) for x in counts) if counts else 0
                freq_dict[ngram] = total
        if not freq_dict:
            messagebox.showerror("에러", "워드클라우드 생성을 위한 유효한 데이터가 없습니다.")
            return
        font_path = "C:\\Windows\\Fonts\\msyh.ttc"
        wc = WordCloud(font_path=font_path, width=800, height=600,
                       background_color="white", color_func=diverse_color_func)
        wc.generate_from_frequencies(freq_dict)
        wc_window = tk.Toplevel(self.master)
        wc_window.title("워드클라우드")
        fig = plt.Figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        canvas = FigureCanvasTkAgg(fig, master=wc_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        save_img_button = tk.Button(wc_window, text="이미지 저장", command=lambda: self.save_wordcloud_image(wc))
        save_img_button.pack(pady=5)
    
    def save_wordcloud_image(self, wc):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")])
        if file_path:
            wc.to_file(file_path)
            messagebox.showinfo("저장 완료", f"워드클라우드 이미지가 {os.path.basename(file_path)}에 저장되었습니다.")
    
    # --- '비교 결과 적용하기' 관련 ---
    def apply_comparison(self):
        if not self.files_data:
            messagebox.showerror("에러", "먼저 파일 비교를 통해 문헌을 불러와야 합니다.")
            return
        if self.apply_selection_window is not None and self.apply_selection_window.winfo_exists():
            return
        self.cancel_requested = False
        self.apply_selection_window = tk.Toplevel(self.master)
        self.apply_selection_window.title("적용 파일 선택")
        self.apply_selection_window.bind("<Destroy>", lambda e: setattr(self, "apply_selection_window", None))
        tk.Label(self.apply_selection_window, text="적용할 파일을 선택하세요\n(여러 개 선택 가능)").pack(padx=10, pady=10)
        listbox = tk.Listbox(self.apply_selection_window, selectmode=tk.MULTIPLE, width=30)
        for fname in self.files_data.keys():
            listbox.insert(tk.END, fname)
        listbox.pack(padx=10, pady=10)
        def on_select():
            selected_indices = listbox.curselection()
            if not selected_indices:
                messagebox.showerror("에러", "최소 1개 이상의 파일을 선택해야 합니다.")
                return
            selected_files = [listbox.get(i) for i in selected_indices]
            self.apply_selection_window.destroy()
            processing_done = [False]
            def check_processing():
                if not processing_done[0] and not self.cancel_requested:
                    self.show_waiting_popup("작업량에 따라 몇 분 정도 걸릴 수 있습니다. 잠시만 기다려 주세요.")
            self.master.after(2500, check_processing)
            for fname in selected_files:
                if self.cancel_requested:
                    break
                self.open_result_window(fname)
            processing_done[0] = True
            self.close_waiting_popup()
        tk.Button(self.apply_selection_window, text="확인", command=on_select).pack(padx=10, pady=10)
    
    def count_red_chars(self, widget):
        intervals = self.get_tag_ranges(widget, "red")
        return sum(end - start for start, end in intervals)
    
    def open_result_window(self, fname):
        if self.cancel_requested:
            return
        win = tk.Toplevel(self.master)
        win.title(f"{fname} 비교 결과 적용")
        orig_text = self.original_text_data[fname]
        processed_text = self.files_data[fname]
        index_mapping = self.index_map[fname]
        total_count = len(index_mapping)
        result_content = self.result_text.get("1.0", tk.END)
        edited_ngram_set = set()
        for line in result_content.splitlines():
            if line.strip():
                ngram = line.split(":")[0].strip()
                if ngram:
                    edited_ngram_set.add(ngram)
        info_frame = tk.Frame(win)
        info_frame.pack(padx=10, pady=5, fill=tk.X)
        total_label = tk.Label(info_frame, text=f"전체 한자수: {total_count}자")
        total_label.pack(side=tk.LEFT, padx=5)
        red_label = tk.Label(info_frame, text="해당 글자수: 계산중...", fg="black")
        red_label.pack(side=tk.LEFT, padx=5)
        ratio_label = tk.Label(info_frame, text="비율: 계산중...")
        ratio_label.pack(side=tk.LEFT, padx=5)
        text_frame = tk.Frame(win)
        text_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar = tk.Scrollbar(text_frame, command=text_widget.yview)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=v_scrollbar.set)
        text_widget.insert(tk.END, orig_text)
        text_widget.tag_configure("red", foreground="red")
        text_widget.tag_configure("black", foreground="black")
        red_positions = set()
        for ngram in edited_ngram_set:
            if self.cancel_requested:
                break
            start_idx = 0
            while True:
                if self.cancel_requested:
                    break
                pos = processed_text.find(ngram, start_idx)
                if pos == -1:
                    break
                for offset in range(len(ngram)):
                    if pos + offset < len(index_mapping):
                        red_positions.add(index_mapping[pos + offset])
                start_idx = pos + 1
        for pos in red_positions:
            if self.cancel_requested:
                break
            index_str = f"1.0+{pos}c"
            text_widget.tag_add("red", index_str, f"{index_str}+1c")
        red_count = self.count_red_chars(text_widget)
        ratio = (red_count / total_count * 100) if total_count > 0 else 0
        ratio = min(ratio, 100.00)
        red_label.config(text=f"해당 글자수: {red_count}자")
        ratio_label.config(text=f"비율: {ratio:.2f}%")
        def save_data():
            file_path = filedialog.asksaveasfilename(defaultextension=".html",
                                                     filetypes=[("HTML files", "*.html"),
                                                                ("Text files", "*.txt"),
                                                                ("HWP files", "*.hwp")])
            if file_path:
                def worker():
                    full_text = text_widget.get("1.0", "end-1c")
                    result_html = (
                        "<html><head><meta charset='utf-8'>"
                        "<style>"
                        "body { margin:0; padding:0; } "
                        "div { font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; font-size:11pt; line-height:1.5; overflow-y: scroll; overflow-x: hidden; height:100vh; white-space: pre-wrap; }"
                        "</style></head><body><div>"
                    )
                    i = 0
                    while i < len(full_text):
                        if self.cancel_requested:
                            return
                        index = "1.0+{}c".format(i)
                        tags = text_widget.tag_names(index)
                        current_color = "red" if "red" in tags else "black"
                        j = i + 1
                        while j < len(full_text):
                            next_index = "1.0+{}c".format(j)
                            next_tags = text_widget.tag_names(next_index)
                            if (("red" in next_tags) == ("red" in tags)):
                                j += 1
                            else:
                                break
                        segment = full_text[i:j]
                        result_html += '<span style="color: {};">{}</span>'.format(current_color, html.escape(segment))
                        i = j
                    result_html += "</div></body></html>"
                    try:
                        if self.cancel_requested:
                            return
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(result_html)
                        self.master.after(0, lambda: messagebox.showinfo("저장 완료", f"데이터가 {os.path.basename(file_path)}에 저장되었습니다."))
                    except Exception as e:
                        self.master.after(0, lambda: messagebox.showerror("저장 에러", f"파일 저장 중 오류 발생: {str(e)}"))
                    finally:
                        self.master.after(0, self.close_waiting_popup)
                self.cancel_requested = False
                thread = threading.Thread(target=worker)
                thread.start()
                self.master.after(2500, lambda: self.show_waiting_popup() if thread.is_alive() and not self.cancel_requested else None)
        tk.Button(win, text="데이터 저장하기", command=save_data).pack(padx=10, pady=5)
        self.close_waiting_popup()
    
    def get_tag_ranges(self, widget, tag):
        ranges = widget.tag_ranges(tag)
        intervals = []
        for i in range(0, len(ranges), 2):
            start_offset = int(widget.count("1.0", ranges[i], "chars")[0])
            end_offset = int(widget.count("1.0", ranges[i+1], "chars")[0])
            intervals.append((start_offset, end_offset))
        intervals.sort()
        merged = []
        for interval in intervals:
            if not merged:
                merged.append(interval)
            else:
                last = merged[-1]
                if interval[0] <= last[1]:
                    merged[-1] = (last[0], max(last[1], interval[1]))
                else:
                    merged.append(interval)
        return merged

if __name__ == "__main__":
    root = tk.Tk()
    app = NgramAnalyzer(root)
    root.mainloop()
