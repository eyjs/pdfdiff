#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 재업로드 및 재검사 기능 모듈
기존 PDF 검증 GUI에 통합할 수 있는 기능들
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import datetime

class PDFReloadHandler:
    """PDF 재업로드 및 연속 검사 핸들러"""
    
    def __init__(self, validator_gui_instance):
        self.gui = validator_gui_instance
        self.validation_history = []
        self.setup_reload_ui()
    
    def setup_reload_ui(self):
        """재업로드 UI 요소 추가"""
        # 기존 UI에 추가할 프레임 생성
        if hasattr(self.gui, 'main_frame'):
            # PDF 재선택 프레임
            reload_frame = ttk.LabelFrame(self.gui.main_frame, text="PDF 재선택", padding=10)
            reload_frame.pack(fill=tk.X, pady=(10,0))
            
            # 새 PDF 선택 버튼
            btn_frame = ttk.Frame(reload_frame)
            btn_frame.pack(fill=tk.X)
            
            self.reload_btn = ttk.Button(btn_frame, 
                                        text="🔄 다른 PDF로 재검사",
                                        command=self.reload_pdf)
            self.reload_btn.pack(side=tk.LEFT)
            
            # 연속 검사 모드
            self.continuous_var = tk.BooleanVar()
            continuous_check = ttk.Checkbutton(btn_frame,
                                              text="연속 검사 모드",
                                              variable=self.continuous_var)
            continuous_check.pack(side=tk.LEFT, padx=(20,0))
            
            # 빠른 재검사 버튼  
            quick_btn = ttk.Button(btn_frame,
                                  text="⚡ 현재 PDF 재검사",
                                  command=self.quick_revalidate)
            quick_btn.pack(side=tk.RIGHT)
            
            # 검사 이력 프레임
            history_frame = ttk.LabelFrame(self.gui.main_frame, text="검사 이력", padding=10)
            history_frame.pack(fill=tk.X, pady=(10,0))
            
            # 이력 리스트박스
            history_list_frame = ttk.Frame(history_frame)
            history_list_frame.pack(fill=tk.X)
            
            self.history_listbox = tk.Listbox(history_list_frame, height=4)
            history_scroll = ttk.Scrollbar(history_list_frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
            self.history_listbox.config(yscrollcommand=history_scroll.set)
            
            self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 이력 관리 버튼
            history_btn_frame = ttk.Frame(history_frame)
            history_btn_frame.pack(fill=tk.X, pady=(10,0))
            
            ttk.Button(history_btn_frame, text="선택 항목 재검사",
                      command=self.revalidate_from_history).pack(side=tk.LEFT)
            
            ttk.Button(history_btn_frame, text="이력 지우기",
                      command=self.clear_history).pack(side=tk.RIGHT)
    
    def reload_pdf(self):
        """새 PDF 선택하여 재검사"""
        # 현재 PDF 경로가 있으면 그 폴더를 기본으로 설정
        initial_dir = None
        if hasattr(self.gui, 'filled_pdf_path'):
            initial_dir = os.path.dirname(self.gui.filled_pdf_path)
        
        new_pdf_path = filedialog.askopenfilename(
            title="재검사할 PDF 선택",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=initial_dir
        )
        
        if new_pdf_path:
            # 현재 세션 백업
            self.backup_current_session()
            
            # 새 PDF로 업데이트
            self.gui.filled_pdf_path = new_pdf_path
            
            # GUI 업데이트 (기존 PDF 표시 라벨 업데이트)
            if hasattr(self.gui, 'pdf_file_label'):
                self.gui.pdf_file_label.config(text=f"선택된 PDF: {os.path.basename(new_pdf_path)}")
            
            # 로그 출력
            if hasattr(self.gui, 'log'):
                self.gui.log(f"새 PDF 선택됨: {os.path.basename(new_pdf_path)}")
            
            # 연속 검사 모드면 자동 검증
            if self.continuous_var.get():
                self.gui.root.after(500, self.auto_validate)
            else:
                # 수동 모드면 검증 버튼 활성화
                if hasattr(self.gui, 'validate_btn'):
                    self.gui.validate_btn.config(state='normal')
                if hasattr(self.gui, 'log'):
                    self.gui.log("검증 버튼을 클릭하여 재검사하세요.")
    
    def auto_validate(self):
        """자동 검증 실행"""
        if hasattr(self.gui, 'run_validation'):
            self.gui.run_validation()
    
    def quick_revalidate(self):
        """현재 PDF로 즉시 재검사"""
        if hasattr(self.gui, 'filled_pdf_path') and hasattr(self.gui, 'run_validation'):
            if hasattr(self.gui, 'log'):
                self.gui.log("=== 빠른 재검사 시작 ===")
            self.gui.run_validation()
        else:
            messagebox.showinfo("안내", "먼저 템플릿과 PDF를 선택해주세요.")
    
    def backup_current_session(self):
        """현재 검증 세션 백업"""
        if hasattr(self.gui, 'filled_pdf_path') and hasattr(self.gui, 'validator'):
            session_data = {
                'pdf_path': self.gui.filled_pdf_path,
                'pdf_name': os.path.basename(self.gui.filled_pdf_path),
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'template_name': getattr(self.gui, 'selected_template_name', 'Unknown'),
                'results_summary': self.get_results_summary()
            }
            
            self.validation_history.append(session_data)
            self.update_history_display()
    
    def get_results_summary(self):
        """검증 결과 요약 생성"""
        if hasattr(self.gui, 'validator') and hasattr(self.gui.validator, 'validation_results'):
            results = self.gui.validator.validation_results
            total = len(results)
            failed = len([r for r in results if r.get('status') != 'OK'])
            return {
                'total': total,
                'failed': failed,
                'success_rate': ((total - failed) / total * 100) if total > 0 else 0
            }
        return {'total': 0, 'failed': 0, 'success_rate': 0}
    
    def update_history_display(self):
        """검사 이력 표시 업데이트"""
        self.history_listbox.delete(0, tk.END)
        
        # 최근 10개만 표시
        recent_history = self.validation_history[-10:]
        for i, session in enumerate(recent_history, 1):
            summary = session.get('results_summary', {})
            failed = summary.get('failed', 0)
            total = summary.get('total', 0)
            
            status_text = "✅ 통과" if failed == 0 else f"❌ {failed}/{total} 실패"
            display_text = f"{session['pdf_name']} ({session['timestamp']}) - {status_text}"
            
            self.history_listbox.insert(tk.END, display_text)
    
    def revalidate_from_history(self):
        """이력에서 선택한 PDF 재검사"""
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showinfo("안내", "재검사할 항목을 선택해주세요.")
            return
        
        # 선택된 세션 정보 가져오기
        recent_history = self.validation_history[-10:]
        selected_session = recent_history[selection[0]]
        pdf_path = selected_session['pdf_path']
        
        if os.path.exists(pdf_path):
            # PDF 경로 업데이트
            self.gui.filled_pdf_path = pdf_path
            
            # GUI 업데이트
            if hasattr(self.gui, 'pdf_file_label'):
                self.gui.pdf_file_label.config(text=f"선택된 PDF: {os.path.basename(pdf_path)}")
            
            # 재검사 실행
            if hasattr(self.gui, 'log'):
                self.gui.log(f"이력에서 재검사: {os.path.basename(pdf_path)}")
            
            self.gui.run_validation()
        else:
            messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{pdf_path}")
    
    def clear_history(self):
        """검사 이력 지우기"""
        if messagebox.askyesno("확인", "모든 검사 이력을 삭제하시겠습니까?"):
            self.validation_history = []
            self.history_listbox.delete(0, tk.END)
            if hasattr(self.gui, 'log'):
                self.gui.log("검사 이력이 삭제되었습니다.")

# 사용 예시: 기존 PDFValidatorGUI 클래스에 통합
"""
기존 PDFValidatorGUI.__init__에 추가:

def __init__(self, root):
    # ... 기존 초기화 코드 ...
    
    # 재업로드 핸들러 추가
    self.reload_handler = PDFReloadHandler(self)

그리고 기존 run_validation 메서드를 다음과 같이 수정:

def run_validation(self):
    # 기존 검증 로직 실행
    # ... 기존 코드 ...
    
    # 검증 완료 후 재업로드 버튼 활성화
    if hasattr(self, 'reload_handler'):
        self.reload_handler.reload_btn.config(state='normal')
"""
