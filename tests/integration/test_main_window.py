
import tkinter as tk
import unittest
import json
import os
from unittest.mock import patch, call
from tkinter import ttk
from app.gui.main_window import MainWindow
from app.controllers.template_controller import TemplateController
from app.controllers.validation_controller import ValidationController
from infrastructure.repositories.json_template_repository import JsonTemplateRepository
from domain.services.template_service import TemplateService

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.test_templates_file = 'test_templates.json'
        with open(self.test_templates_file, 'w') as f:
            json.dump({}, f)
        self.test_repo = JsonTemplateRepository(file_path=self.test_templates_file)

    def tearDown(self):
        if self.root:
            self.root.destroy()
            self.root = None
        if os.path.exists(self.test_templates_file):
            os.remove(self.test_templates_file)

    def find_button(self, root, text):
        widget_queue = list(root.winfo_children())
        while widget_queue:
            widget = widget_queue.pop(0)
            try:
                if text in widget.cget("text"):
                    return widget
            except tk.TclError:
                pass  # Ignore widgets that don't have a "text" property
            widget_queue.extend(widget.winfo_children())
        return None

    def patched_template_init(self, instance):
        TemplateController.__init__(instance)
        instance.template_repository = self.test_repo
        instance.template_service = TemplateService(instance.template_repository)

    def patched_validation_init(self, instance):
        ValidationController.__init__(instance)
        instance.template_repository = self.test_repo
        instance.template_service = TemplateService(instance.template_repository)

    @patch('tkinter.messagebox.showerror')
    def test_open_template_manager_and_check_for_errors(self, mock_showerror):
        with patch.object(TemplateController, '__init__', self.patched_template_init):
            app = MainWindow(self.root)
            app.open_template_manager()
            self.root.update_idletasks()
            self.root.update()

            toplevel_windows = app.root.winfo_children()
            template_manager_window = None
            for w in toplevel_windows:
                if isinstance(w, tk.Toplevel):
                    template_manager_window = w
                    break
            
            self.assertIsNotNone(template_manager_window, "Template manager window not created")
            app.open_template_manager()
            self.root.update_idletasks()
            self.root.update()

            toplevel_windows = app.root.winfo_children()
            template_manager_window = None
            for w in toplevel_windows:
                if isinstance(w, tk.Toplevel):
                    template_manager_window = w
                    break
            
            self.assertIsNotNone(template_manager_window, "Template manager window not created")
            app.open_template_manager()
            self.root.update_idletasks()
            self.root.update()

            toplevel_windows = app.root.winfo_children()
            template_manager_window = None
            for w in toplevel_windows:
                if isinstance(w, tk.Toplevel):
                    template_manager_window = w
                    break
            
            self.assertIsNotNone(template_manager_window, "Template manager window not created")
            self.assertEqual(template_manager_window.title(), "템플릿 관리자")
            mock_showerror.assert_not_called()

    @patch('tkinter.filedialog.askopenfilename', return_value='test.pdf')
    @patch('tkinter.simpledialog.askstring', return_value='test_template')
    @patch('app.controllers.template_controller.TemplateController.update_status')
    @patch('tkinter.messagebox.showinfo')
    def test_create_new_template(self, mock_showinfo, mock_update_status, mock_askstring, mock_askopenfilename):
        with patch.object(TemplateController, '__init__', self.patched_template_init):
            app = MainWindow(self.root)
            app.open_template_manager()
            self.root.update_idletasks()
            self.root.update()

            create_button = self.find_button(app.root, "새 템플릿 생성")
            self.assertIsNotNone(create_button, "Create button not found")
            create_button.invoke()

            calls = [call("템플릿 'test_template'이 생성되었습니다."), call('1개의 템플릿이 있습니다.')]
            mock_update_status.assert_has_calls(calls, any_order=True)

    @patch('tkinter.messagebox.showerror')
    def test_open_validation_tool(self, mock_showerror):
        with patch.object(ValidationController, '__init__', self.patched_validation_init):
            app = MainWindow(self.root)
            app.open_validation_tool()
            self.root.update_idletasks()
            self.root.update()

            toplevel_windows = app.root.winfo_children()
            validation_tool_window = None
            for w in toplevel_windows:
                if isinstance(w, tk.Toplevel):
                    validation_tool_window = w
                    break
            
            self.assertIsNotNone(validation_tool_window, "Validation tool window not created")
            self.assertEqual(validation_tool_window.title(), "PDF 검증 도구")
            mock_showerror.assert_not_called()

    @patch('tkinter.messagebox.showinfo')
    def test_open_settings(self, mock_showinfo):
        app = MainWindow(self.root)
        app.open_settings()
        self.root.update_idletasks()
        self.root.update()

        toplevel_windows = app.root.winfo_children()
        settings_window = None
        for w in toplevel_windows:
            if isinstance(w, tk.Toplevel):
                settings_window = w
                break
        
        self.assertIsNotNone(settings_window, "Settings window not created")
        self.assertEqual(settings_window.title(), "설정")
            mock_showerror.assert_not_called()

    @patch('tkinter.filedialog.askopenfilename', return_value='test.pdf')
    @patch('tkinter.simpledialog.askstring', return_value='test_template')
    @patch('app.controllers.template_controller.TemplateController.update_status')
    @patch('tkinter.messagebox.showinfo')
    def test_create_new_template(self, mock_showinfo, mock_update_status, mock_askstring, mock_askopenfilename):
        with patch.object(TemplateController, '__init__', self.patched_template_init):
            app = MainWindow(self.root)
            app.open_template_manager()
            self.root.update_idletasks()
            self.root.update()

            create_button = self.find_button(app.root, "새 템플릿 생성")
            self.assertIsNotNone(create_button, "Create button not found")
            create_button.invoke()

            calls = [call("템플릿 'test_template'이 생성되었습니다."), call('1개의 템플릿이 있습니다.')]
            mock_update_status.assert_has_calls(calls, any_order=True)

    @patch('tkinter.messagebox.showerror')
    def test_open_validation_tool(self, mock_showerror):
        with patch.object(ValidationController, '__init__', self.patched_validation_init):
            app = MainWindow(self.root)
            app.open_validation_tool()
            self.root.update_idletasks()
            self.root.update()

            toplevel_windows = app.root.winfo_children()
            validation_tool_window = None
            for w in toplevel_windows:
                if isinstance(w, tk.Toplevel):
                    validation_tool_window = w
                    break
            
            self.assertIsNotNone(validation_tool_window, "Validation tool window not created")
            self.assertEqual(validation_tool_window.title(), "PDF 검증 도구")
            mock_showerror.assert_not_called()

    @patch('tkinter.messagebox.showinfo')
    def test_open_settings(self, mock_showinfo):
        app = MainWindow(self.root)
        app.open_settings()
        self.root.update_idletasks()
        self.root.update()

        toplevel_windows = app.root.winfo_children()
        settings_window = None
        for w in toplevel_windows:
            if isinstance(w, tk.Toplevel):
                settings_window = w
                break
        
        self.assertIsNotNone(settings_window, "Settings window not created")
        self.assertEqual(settings_window.title(), "설정")
            mock_showerror.assert_not_called()

    @patch('tkinter.filedialog.askopenfilename', return_value='test.pdf')
    @patch('tkinter.simpledialog.askstring', return_value='test_template')
    @patch('app.controllers.template_controller.TemplateController.update_status')
    @patch('tkinter.messagebox.showinfo')
    def test_create_new_template(self, mock_showinfo, mock_update_status, mock_askstring, mock_askopenfilename):
        with patch.object(TemplateController, '__init__', self.patched_template_init):
            app = MainWindow(self.root)
            app.open_template_manager()
            self.root.update_idletasks()
            self.root.update()

            create_button = self.find_button(app.root, "새 템플릿 생성")
            self.assertIsNotNone(create_button, "Create button not found")
            create_button.invoke()

            calls = [call("템플릿 'test_template'이 생성되었습니다."), call('1개의 템플릿이 있습니다.')]
            mock_update_status.assert_has_calls(calls, any_order=True)

    @patch('tkinter.messagebox.showerror')
    def test_open_validation_tool(self, mock_showerror):
        with patch.object(ValidationController, '__init__', self.patched_validation_init):
            app = MainWindow(self.root)
            app.open_validation_tool()
            self.root.update_idletasks()
            self.root.update()

            toplevel_windows = app.root.winfo_children()
            validation_tool_window = None
            for w in toplevel_windows:
                if isinstance(w, tk.Toplevel):
                    validation_tool_window = w
                    break
            
            self.assertIsNotNone(validation_tool_window, "Validation tool window not created")
            self.assertEqual(validation_tool_window.title(), "PDF 검증 도구")
            mock_showerror.assert_not_called()

    @patch('tkinter.messagebox.showinfo')
    def test_open_settings(self, mock_showinfo):
        app = MainWindow(self.root)
        app.open_settings()
        self.root.update_idletasks()
        self.root.update()

        toplevel_windows = app.root.winfo_children()
        settings_window = None
        for w in toplevel_windows:
            if isinstance(w, tk.Toplevel):
                settings_window = w
                break
        
        self.assertIsNotNone(settings_window, "Settings window not created")
        self.assertEqual(settings_window.title(), "설정")

    @patch('tkinter.messagebox.showinfo')
    def test_show_help(self, mock_showinfo):
        app = MainWindow(self.root)
        app.show_help()
        mock_showinfo.assert_called_once_with("도움말", unittest.mock.ANY)

    @patch('tkinter.messagebox.showinfo')
    def test_show_about(self, mock_showinfo):
        app = MainWindow(self.root)
        app.show_about()
        mock_showinfo.assert_called_once_with("정보", unittest.mock.ANY)

if __name__ == '__main__':
    unittest.main()


