import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, colorchooser, Listbox, Scrollbar, Toplevel
import fitz  # PyMuPDF
from PIL import Image, ImageTk, ImageDraw
import json
import os
import shutil

class ROISelector(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill=tk.BOTH, expand=True)

        self.pdf_path = None
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.rois = {}  # Store ROIs for all pages
        self.roi_items = {}  # Canvas item IDs for ROIs on the current page
        self.current_rect = None
        self.start_x = None
        self.start_y = None
        self.zoom_factor = 1.0
        self.tk_images = []
        self.original_images = []

        self.roi_color = "red"
        self.roi_name_prefix = "ROI"
        self.templates = {}
        self.templates_file = "roi_templates.json"


        self.setup_ui()
        self.bind_events()
        self.load_templates_from_file()

    def setup_ui(self):
        # Top control frame
        self.controls_frame = tk.Frame(self)
        self.controls_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.btn_open = tk.Button(self.controls_frame, text="PDF 열기", command=self.open_pdf)
        self.btn_open.pack(side=tk.LEFT, padx=5)

        self.btn_prev = tk.Button(self.controls_frame, text="이전 페이지", command=self.prev_page, state=tk.DISABLED)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.page_label = tk.Label(self.controls_frame, text="0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.btn_next = tk.Button(self.controls_frame, text="다음 페이지", command=self.next_page, state=tk.DISABLED)
        self.btn_next.pack(side=tk.LEFT, padx=5)

        self.btn_zoom_in = tk.Button(self.controls_frame, text="확대 (+)", command=self.zoom_in, state=tk.DISABLED)
        self.btn_zoom_in.pack(side=tk.LEFT, padx=5)

        self.btn_zoom_out = tk.Button(self.controls_frame, text="축소 (-)", command=self.zoom_out, state=tk.DISABLED)
        self.btn_zoom_out.pack(side=tk.LEFT, padx=5)

        self.btn_color = tk.Button(self.controls_frame, text="ROI 색상 변경", command=self.choose_roi_color)
        self.btn_color.pack(side=tk.LEFT, padx=5)

        self.btn_save_template = tk.Button(self.controls_frame, text="템플릿 저장", command=self.save_template)
        self.btn_save_template.pack(side=tk.LEFT, padx=5)

        btn_show_templates = tk.Button(self.controls_frame, text="템플릿 목록", command=self.show_template_list)
        btn_show_templates.pack(side=tk.LEFT, padx=(0,5))


        self.btn_export = tk.Button(self.controls_frame, text="ROI 정보 내보내기", command=self.export_rois)
        self.btn_export.pack(side=tk.RIGHT, padx=5)

        # Canvas for PDF display
        self.canvas = tk.Canvas(self, bg="gray")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ROI Listbox
        self.roi_list_frame = tk.Frame(self, bd=1, relief=tk.SUNKEN)
        self.roi_list_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        tk.Label(self.roi_list_frame, text="ROI 목록").pack()

        self.roi_listbox = Listbox(self.roi_list_frame, width=30)
        self.roi_listbox.pack(fill=tk.Y, expand=True)

        self.btn_delete_roi = tk.Button(self.roi_list_frame, text="선택 ROI 삭제", command=self.delete_selected_roi)
        self.btn_delete_roi.pack(fill=tk.X)
        self.btn_rename_roi = tk.Button(self.roi_list_frame, text="선택 ROI 이름 변경", command=self.rename_selected_roi)
        self.btn_rename_roi.pack(fill=tk.X)


    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.master.bind("<Configure>", self.on_resize) # Bind to window resize
        self.roi_listbox.bind('<<ListboxSelect>>', self.on_roi_select)


    def on_resize(self, event=None):
        if self.doc:
            self.display_page()


    def open_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if not path:
            return

        self.pdf_path = path
        self.doc = fitz.open(self.pdf_path)
        self.total_pages = len(self.doc)
        self.current_page = 0
        self.rois = {}
        self.zoom_factor = 1.0

        # Cache original images
        self.original_images = [page.get_pixmap() for page in self.doc]

        self.update_navigation()
        self.display_page()
        self.update_roi_listbox()


    def display_page(self):
        if not self.doc:
            return

        self.canvas.delete("all")
        self.roi_items = {}

        pix = self.original_images[self.current_page]

        # Calculate aspect ratios
        img_aspect = pix.width / pix.height
        canvas_aspect = self.canvas.winfo_width() / self.canvas.winfo_height()

        # Determine scaling factor to fit image in canvas
        if img_aspect > canvas_aspect:
            # Fit to width
            new_width = self.canvas.winfo_width()
            new_height = int(new_width / img_aspect)
        else:
            # Fit to height
            new_height = self.canvas.winfo_height()
            new_width = int(new_height * img_aspect)

        self.scale_factor_x = new_width / pix.width
        self.scale_factor_y = new_height / pix.height

        # Apply zoom
        zoomed_width = int(new_width * self.zoom_factor)
        zoomed_height = int(new_height * self.zoom_factor)

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_resized = img.resize((zoomed_width, zoomed_height), Image.LANCZOS)

        # Keep a reference to the image to prevent it from being garbage collected
        tk_img = ImageTk.PhotoImage(img_resized)
        self.tk_images.append(tk_img) # Store reference

        self.canvas.config(scrollregion=(0, 0, zoomed_width, zoomed_height))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)

        self.draw_rois_for_current_page()
        self.update_roi_listbox()


    def draw_rois_for_current_page(self):
        page_rois = self.rois.get(self.current_page, {})
        for name, data in page_rois.items():
            coords = data['coords']
            color = data['color']

            # Apply scaling and zoom to the stored PDF coordinates
            x1 = coords[0] * self.scale_factor_x * self.zoom_factor
            y1 = coords[1] * self.scale_factor_y * self.zoom_factor
            x2 = coords[2] * self.scale_factor_x * self.zoom_factor
            y2 = coords[3] * self.scale_factor_y * self.zoom_factor

            rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)
            label = self.canvas.create_text(x1, y1, text=name, anchor=tk.SW, fill=color)
            self.roi_items[name] = {'rect': rect, 'label': label, 'color': color}


    def update_navigation(self):
        self.page_label.config(text=f"{self.current_page + 1} / {self.total_pages}")
        self.btn_prev.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.btn_next.config(state=tk.NORMAL if self.current_page < self.total_pages - 1 else tk.DISABLED)
        self.btn_zoom_in.config(state=tk.NORMAL if self.doc else tk.DISABLED)
        self.btn_zoom_out.config(state=tk.NORMAL if self.doc else tk.DISABLED)


    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_navigation()
            self.display_page()


    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_navigation()
            self.display_page()


    def zoom_in(self):
        self.zoom_factor *= 1.2
        self.display_page()


    def zoom_out(self):
        self.zoom_factor /= 1.2
        self.display_page()


    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline=self.roi_color, width=2)


    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)


    def on_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)

        # Ensure start is top-left and end is bottom-right
        x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
        x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)

        # Ignore tiny accidental drags
        if abs(x1 - x2) < 5 or abs(y1 - y2) < 5:
            self.canvas.delete(self.current_rect)
            self.current_rect = None
            return

        # Convert canvas coordinates back to original PDF coordinates
        orig_x1 = x1 / (self.scale_factor_x * self.zoom_factor)
        orig_y1 = y1 / (self.scale_factor_y * self.zoom_factor)
        orig_x2 = x2 / (self.scale_factor_x * self.zoom_factor)
        orig_y2 = y2 / (self.scale_factor_y * self.zoom_factor)

        # Generate a unique name for the ROI
        roi_num = 1
        while f"{self.roi_name_prefix}_{roi_num}" in self.rois.get(self.current_page, {}):
            roi_num += 1
        new_roi_name = f"{self.roi_name_prefix}_{roi_num}"

        # Get the ROI data
        roi_data = {
            "coords": (orig_x1, orig_y1, orig_x2, orig_y2),
            "color": self.roi_color
        }

        # Add to the main ROIs dictionary
        if self.current_page not in self.rois:
            self.rois[self.current_page] = {}
        self.rois[self.current_page][new_roi_name] = roi_data

        # Add to canvas items
        label = self.canvas.create_text(x1, y1, text=new_roi_name, anchor=tk.SW, fill=self.roi_color)
        self.roi_items[new_roi_name] = {'rect': self.current_rect, 'label': label, 'color': self.roi_color}
        self.current_rect = None

        self.update_roi_listbox()


    def update_roi_listbox(self):
        self.roi_listbox.delete(0, tk.END)
        page_rois = self.rois.get(self.current_page, {})
        for name in sorted(page_rois.keys()):
            self.roi_listbox.insert(tk.END, name)


    def delete_selected_roi(self):
        selected_indices = self.roi_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("경고", "삭제할 ROI를 선택하세요.")
            return

        selected_roi_name = self.roi_listbox.get(selected_indices[0])

        # Delete from main dictionary
        if self.current_page in self.rois and selected_roi_name in self.rois[self.current_page]:
            del self.rois[self.current_page][selected_roi_name]

        # Delete from canvas
        if selected_roi_name in self.roi_items:
            item = self.roi_items.pop(selected_roi_name)
            self.canvas.delete(item['rect'])
            self.canvas.delete(item['label'])

        self.update_roi_listbox()


    def rename_selected_roi(self):
        selected_indices = self.roi_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("경고", "이름을 변경할 ROI를 선택하세요.")
            return

        old_name = self.roi_listbox.get(selected_indices[0])
        new_name = simpledialog.askstring("이름 변경", "새로운 ROI 이름을 입력하세요:", initialvalue=old_name)

        if not new_name or new_name == old_name:
            return

        if new_name in self.rois.get(self.current_page, {}):
            messagebox.showerror("오류", "이미 존재하는 이름입니다.")
            return

        # Rename in main dictionary
        page_rois = self.rois.get(self.current_page, {})
        if old_name in page_rois:
            page_rois[new_name] = page_rois.pop(old_name)

        # Rename on canvas
        if old_name in self.roi_items:
            item = self.roi_items.pop(old_name)
            self.canvas.itemconfig(item['label'], text=new_name)
            self.roi_items[new_name] = item

        self.update_roi_listbox()


    def choose_roi_color(self):
        color_code = colorchooser.askcolor(title="ROI 색상 선택")
        if color_code:
            self.roi_color = color_code[1]


    def on_roi_select(self, event):
        selected_indices = self.roi_listbox.curselection()
        if not selected_indices:
            return

        # Reset all ROI borders to normal
        for name, item in self.roi_items.items():
            self.canvas.itemconfig(item['rect'], outline=item['color'], width=2)

        # Highlight the selected one
        selected_roi_name = self.roi_listbox.get(selected_indices[0])
        if selected_roi_name in self.roi_items:
            item = self.roi_items[selected_roi_name]
            self.canvas.itemconfig(item['rect'], outline="blue", width=4)


    def export_rois(self):
        if not self.rois:
            messagebox.showwarning("경고", "내보낼 ROI가 없습니다.")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="ROI 정보 저장"
        )
        if not save_path:
            return

        # Prepare a serializable version of the ROIs
        export_data = {}
        for page_num, page_rois in self.rois.items():
            export_data[str(page_num)] = page_rois

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo("성공", f"ROI 정보가 '{save_path}'에 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"파일 저장 중 오류 발생: {e}")

    def save_template(self):
        if not self.rois:
            messagebox.showwarning("경고", "템플릿으로 저장할 ROI가 없습니다.")
            return

        template_name = simpledialog.askstring("템플릿 저장", "템플릿 이름을 입력하세요:")
        if not template_name:
            return

        if template_name in self.templates and not messagebox.askyesno("덮어쓰기 확인", f"'{template_name}' 템플릿이 이미 존재합니다. 덮어쓰시겠습니까?"):
            return

        # Prepare a serializable version of the ROIs for the template
        template_data = {}
        for page_num, page_rois in self.rois.items():
            template_data[str(page_num)] = {name: data for name, data in page_rois.items()}

        self.templates[template_name] = template_data
        self.save_templates_to_file()
        messagebox.showinfo("성공", f"'{template_name}' 템플릿이 저장되었습니다.")

    def load_template(self, template_name):
        if not self.doc:
            messagebox.showwarning("경고", "템플릿을 적용할 PDF 파일을 먼저 열어주세요.")
            return

        if template_name not in self.templates:
            messagebox.showerror("오류", f"'{template_name}' 템플릿을 찾을 수 없습니다.")
            return

        template_data = self.templates[template_name]

        self.rois = {}
        for page_num_str, page_rois in template_data.items():
            page_num = int(page_num_str)
            self.rois[page_num] = page_rois

        self.display_page() # This will redraw ROIs and update the listbox
        messagebox.showinfo("성공", f"'{template_name}' 템플릿을 불러왔습니다.")

    def save_templates_to_file(self):
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=4)
        except Exception as e:
            print(f"템플릿 파일 저장 오류: {e}")

    def load_templates_from_file(self):
        if os.path.exists(self.templates_file):
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"템플릿 파일 불러오기 오류: {e}")
                self.templates = {}

    # This function is now correctly inside the class.
    def show_template_list(self):
        if not self.templates:
            messagebox.showinfo("템플릿 없음", "저장된 템플릿이 없습니다.")
            return

        template_window = Toplevel(self.master)
        template_window.title("템플릿 목록")

        listbox = Listbox(template_window, width=50, height=15)
        listbox.pack(pady=10, padx=10)

        for name in self.templates.keys():
            listbox.insert(tk.END, name)

        def load_selected():
            selected_indices = listbox.curselection()
            if not selected_indices:
                return
            selected_template_name = listbox.get(selected_indices[0])
            self.load_template(selected_template_name)
            template_window.destroy()

        def delete_selected():
            selected_indices = listbox.curselection()
            if not selected_indices:
                return
            selected_template_name = listbox.get(selected_indices[0])
            if messagebox.askyesno("삭제 확인", f"'{selected_template_name}' 템플릿을 삭제하시겠습니까?"):
                del self.templates[selected_template_name]
                self.save_templates_to_file()
                listbox.delete(selected_indices[0])
                messagebox.showinfo("삭제 완료", f"'{selected_template_name}' 템플릿이 삭제되었습니다.")


        btn_frame = tk.Frame(template_window)
        btn_frame.pack(pady=5)

        load_btn = tk.Button(btn_frame, text="불러오기", command=load_selected)
        load_btn.pack(side=tk.LEFT, padx=5)

        delete_btn = tk.Button(btn_frame, text="삭제", command=delete_selected)
        delete_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(btn_frame, text="닫기", command=template_window.destroy)
        close_btn.pack(side=tk.LEFT, padx=5)


def main():
    root = tk.Tk()
    root.title("ROI Selector for PDF")
    root.geometry("1200x800")
    app = ROISelector(root)
    root.mainloop()

if __name__ == "__main__":
    main()