from __future__ import annotations

import importlib.util
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any


def _load_module(filename: str, module_name: str) -> Any:
    module_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Không thể nạp module từ {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module_6A = _load_module("6A.py", "chapter6_module_6A")
module_6B = _load_module("6B.py", "chapter6_module_6B")
module_6C = _load_module("6C.py", "chapter6_module_6C")

InvertedIndexBuilder = module_6A.InvertedIndexBuilder
SingleWordFinder = module_6B.SingleWordFinder
WordFileFinder = module_6C.WordFileFinder
AdvancedQueryFinder = module_6C.AdvancedQueryFinder


class Chapter6DemoApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Chapter 6 - Demo Inverted Index")
        self.root.geometry("1360x860")

        self.builder = InvertedIndexBuilder()
        self.index_data = None

        base_dir = Path(__file__).resolve().parent
        sample_dir = base_dir / "chapter6_sample"
        sample_query = sample_dir / "query.txt"

        self.directory_var = tk.StringVar(value=str(sample_dir))
        self.stoplist_var = tk.StringVar(value="StopList.txt")
        self.output_var = tk.StringVar(value=str(base_dir / "index.json"))
        self.word_var = tk.StringVar(value="cars")
        self.weight_var = tk.StringVar(value="3")
        self.top_n_var = tk.StringVar(value="5")
        self.word_file_var = tk.StringVar(value=str(sample_query))
        self.phrase_var = tk.StringVar(value="cars city")
        self.boolean_query_var = tk.StringVar(value="cars AND city")
        self.use_lemmatization_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Nạp dữ liệu mẫu rồi bấm Tạo index để bắt đầu.")

        self.result_text: tk.Text | None = None
        self._build_layout()

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=12)
        container.grid(sticky="nsew")
        container.columnconfigure(0, weight=2)
        container.columnconfigure(1, weight=3)
        container.rowconfigure(1, weight=1)

        ttk.Label(
            container,
            text="Demo Chapter 6 - Inverted Index và Tìm kiếm",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        control_frame = ttk.Frame(container)
        control_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        control_frame.columnconfigure(0, weight=1)

        self._build_source_frame(control_frame)
        self._build_single_word_frame(control_frame)
        self._build_word_file_frame(control_frame)
        self._build_phrase_frame(control_frame)
        self._build_boolean_frame(control_frame)
        self._build_actions_frame(control_frame)

        result_frame = ttk.LabelFrame(container, text="Kết quả", padding=10)
        result_frame.grid(row=1, column=1, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(1, weight=0)
        result_frame.rowconfigure(0, weight=1)

        self.result_text = tk.Text(
            result_frame,
            width=90,
            height=40,
            font=("Consolas", 11),
            bg="white",
            fg="black",
            insertbackground="black",
            relief="solid",
            borderwidth=1,
            wrap="none",
        )
        self.result_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)

        ttk.Label(container, textvariable=self.status_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 0)
        )

        self._render_intro()

    def _build_source_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Nguồn dữ liệu", padding=10)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Thư mục tài liệu").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.directory_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(frame, text="Chọn thư mục", command=self._choose_directory).grid(row=0, column=2, pady=4)

        ttk.Label(frame, text="Tên file StopList").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.stoplist_var).grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(frame, text="File JSON đầu ra").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(frame, text="Chọn file", command=self._choose_output_file).grid(row=2, column=2, pady=4)

        ttk.Checkbutton(
            frame,
            text="Bật lemmatization (ví dụ: cats -> cat)",
            variable=self.use_lemmatization_var,
            command=self._invalidate_index_cache,
        ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        ttk.Button(frame, text="Nạp ví dụ mẫu", command=self._load_sample_data).grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=(8, 0)
        )

    def _build_single_word_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Tìm theo 1 từ", padding=10)
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Từ khóa").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.word_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(frame, text="Trọng số").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.weight_var).grid(row=1, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(frame, text="Top N").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.top_n_var).grid(row=2, column=1, sticky="ew", padx=6, pady=4)

        ttk.Button(frame, text="Tìm theo 1 từ", command=self.run_single_word_search).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_word_file_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Tìm theo WordFile", padding=10)
        frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Đường dẫn WordFile").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.word_file_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Button(frame, text="Chọn file", command=self._choose_word_file).grid(row=0, column=2, pady=4)

        ttk.Button(frame, text="Tìm theo WordFile", command=self.run_word_file_search).grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0)
        )

    def _build_phrase_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Tìm theo cụm từ", padding=10)
        frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Cụm từ").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.phrase_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Button(frame, text="Tìm phrase", command=self.run_phrase_search).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_boolean_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Tìm theo boolean query", padding=10)
        frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Biểu thức").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.boolean_query_var).grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Button(frame, text="Tìm boolean", command=self.run_boolean_search).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

    def _build_actions_frame(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Thao tác", padding=10)
        frame.grid(row=5, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Button(frame, text="Tạo index", command=self.build_index).grid(
            row=0, column=0, sticky="ew", padx=(0, 4), pady=4
        )
        ttk.Button(frame, text="Lưu index ra JSON", command=self.save_index).grid(
            row=0, column=1, sticky="ew", padx=(4, 0), pady=4
        )
        ttk.Button(frame, text="Xóa màn hình kết quả", command=self._clear_result).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=4
        )

    def _choose_directory(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.directory_var.get() or str(Path(__file__).parent))
        if selected:
            self.directory_var.set(selected)

    def _choose_output_file(self) -> None:
        selected = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=Path(self.output_var.get() or "index.json").name,
        )
        if selected:
            self.output_var.set(selected)

    def _choose_word_file(self) -> None:
        selected = filedialog.askopenfilename(
            initialdir=str(Path(self.word_file_var.get()).parent) if self.word_file_var.get() else str(Path(__file__).parent),
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if selected:
            self.word_file_var.set(selected)

    def _load_sample_data(self) -> None:
        base_dir = Path(__file__).resolve().parent
        sample_dir = base_dir / "chapter6_sample"
        self.directory_var.set(str(sample_dir))
        self.stoplist_var.set("StopList.txt")
        self.output_var.set(str(base_dir / "index.json"))
        self.word_var.set("cars")
        self.weight_var.set("3")
        self.top_n_var.set("5")
        self.word_file_var.set(str(sample_dir / "query.txt"))
        self.phrase_var.set("cars city")
        self.boolean_query_var.set("cars AND city")
        self.use_lemmatization_var.set(True)
        self._invalidate_index_cache()
        self.status_var.set("Đã nạp dữ liệu mẫu của chapter 6.")
        self._render_intro()

    def _render_intro(self) -> None:
        self._set_result(
            "Demo chapter 6 gồm 3 chức năng:\n"
            "1. Tạo inverted index từ thư mục tài liệu.\n"
            "2. Tìm kiếm theo 1 từ với trọng số.\n"
            "3. Tìm kiếm theo WordFile chứa nhiều từ khóa.\n"
            "4. Tìm phrase query theo cụm từ liên tiếp.\n"
            "5. Tìm boolean query với AND / OR / NOT.\n\n"
            "Khi bật lemmatization, các biến thể như 'cats' sẽ được quy về 'cat'.\n\n"
            "Bạn có thể bấm 'Nạp ví dụ mẫu' rồi chạy lần lượt các nút bên trái.\n"
        )

    def _set_result(self, text: str) -> None:
        if self.result_text is None:
            return
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)

    def _append_result(self, text: str) -> None:
        if self.result_text is None:
            return
        self.result_text.insert(tk.END, text)
        self.result_text.see(tk.END)

    def _clear_result(self) -> None:
        self._set_result("")
        self.status_var.set("Đã xóa màn hình kết quả.")

    def _invalidate_index_cache(self) -> None:
        self.index_data = None

    def _require_index(self) -> Any:
        if self.index_data is None:
            self.index_data = self._create_index()
        return self.index_data

    def _create_index(self) -> Any:
        directory = self.directory_var.get().strip()
        stop_list = self.stoplist_var.get().strip()
        if not directory:
            raise ValueError("Bạn cần nhập thư mục tài liệu.")
        if not stop_list:
            raise ValueError("Bạn cần nhập tên file StopList.")
        self.builder.set_lemmatization(self.use_lemmatization_var.get())
        return self.builder.CreateIndex(directory, stop_list)

    def _render_index_summary(self, index_data: Any) -> str:
        lines: list[str] = []
        mode_label = "Lemmatization" if index_data.normalization_mode == "lemma" else "Khớp chính xác"
        lines.append(f"=== CHẾ ĐỘ CHUẨN HÓA: {mode_label} ===")
        lines.append("")
        lines.append("=== DOC TABLE ===")
        for filename, document in sorted(index_data.doc_table.items()):
            lines.append(f"{document.doc_id}. {filename}")

        lines.append("")
        lines.append("=== TERM TABLE ===")
        if not index_data.term_table:
            lines.append("Không có term nào bắt đầu bằng chữ C/c.")
        else:
            lines.extend(index_data.term_table)

        lines.append("")
        lines.append("=== INVERTED INDEX ===")
        if not index_data.inverted_index:
            lines.append("Inverted index rỗng.")
        else:
            for term in index_data.term_table:
                postings = index_data.inverted_index[term]
                rendered = ", ".join(
                    f"{filename}:{frequency}" for filename, frequency in sorted(postings.items())
                )
                lines.append(f"{term} -> {rendered}")

        return "\n".join(lines) + "\n"

    def _render_single_word_results(self, results: list[Any]) -> str:
        lines: list[str] = []
        lines.append("=== KẾT QUẢ TÌM THEO 1 TỪ ===")
        if not results:
            lines.append("Không tìm thấy tài liệu phù hợp.")
            return "\n".join(lines) + "\n"

        for index, result in enumerate(results, start=1):
            lines.append(
                f"{index}. {result.filename} | tần suất = {result.frequency} | điểm = {result.score}"
            )
        return "\n".join(lines) + "\n"

    def _render_word_file_results(self, results: list[Any]) -> str:
        lines: list[str] = []
        lines.append("=== KẾT QUẢ TÌM THEO WORDFILE ===")
        if not results:
            lines.append("Không tìm thấy tài liệu phù hợp.")
            return "\n".join(lines) + "\n"

        for index, result in enumerate(results, start=1):
            terms = ", ".join(
                f"{word}:{frequency}" for word, frequency in sorted(result.matched_terms.items())
            )
            lines.append(f"{index}. {result.filename} | điểm = {result.score} | terms = {terms}")
        return "\n".join(lines) + "\n"

    def _render_phrase_results(self, results: list[Any]) -> str:
        lines: list[str] = []
        lines.append("=== KẾT QUẢ TÌM THEO PHRASE ===")
        if not results:
            lines.append("Không tìm thấy tài liệu chứa cụm từ phù hợp.")
            return "\n".join(lines) + "\n"

        for index, result in enumerate(results, start=1):
            lines.append(f"{index}. {result.filename} | số lần xuất hiện = {result.occurrences}")
        return "\n".join(lines) + "\n"

    def _render_boolean_results(self, results: list[Any]) -> str:
        lines: list[str] = []
        lines.append("=== KẾT QUẢ BOOLEAN QUERY ===")
        if not results:
            lines.append("Không tìm thấy tài liệu phù hợp với boolean query.")
            return "\n".join(lines) + "\n"

        for index, result in enumerate(results, start=1):
            lines.append(f"{index}. {result.filename}")
        return "\n".join(lines) + "\n"

    def build_index(self) -> None:
        try:
            self.index_data = self._create_index()
            rendered = self._render_index_summary(self.index_data)
            self._set_result(rendered)
            self.status_var.set("Đã tạo inverted index thành công.")
        except Exception as error:
            self.status_var.set("Không thể tạo index.")
            messagebox.showerror("Lỗi", str(error))

    def save_index(self) -> None:
        try:
            index_data = self._require_index()
            output_path = self.output_var.get().strip()
            if not output_path:
                raise ValueError("Bạn cần nhập đường dẫn file JSON đầu ra.")

            self.builder.save_index(index_data, output_path)
            rendered = self._render_index_summary(index_data)
            self._set_result(rendered + f"\nĐã lưu index vào: {output_path}\n")
            self.status_var.set("Đã lưu index ra file JSON.")
        except Exception as error:
            self.status_var.set("Không thể lưu index.")
            messagebox.showerror("Lỗi", str(error))

    def run_single_word_search(self) -> None:
        try:
            index_data = self._require_index()
            word = self.word_var.get().strip()
            if not word:
                raise ValueError("Bạn cần nhập từ khóa.")

            weight = int(self.weight_var.get().strip())
            top_n = int(self.top_n_var.get().strip())
            finder = SingleWordFinder(index_data)
            results = finder.Find(word, weight, top_n)

            rendered = self._render_index_summary(index_data)
            rendered += "\n"
            rendered += self._render_single_word_results(results)
            self._set_result(rendered)
            self.status_var.set("Đã chạy tìm kiếm theo 1 từ.")
        except Exception as error:
            self.status_var.set("Không thể tìm theo 1 từ.")
            messagebox.showerror("Lỗi", str(error))

    def run_word_file_search(self) -> None:
        try:
            index_data = self._require_index()
            word_file = self.word_file_var.get().strip()
            if not word_file:
                raise ValueError("Bạn cần nhập đường dẫn WordFile.")

            top_n = int(self.top_n_var.get().strip())
            finder = WordFileFinder(index_data)
            results = finder.Find(word_file, top_n)

            rendered = self._render_index_summary(index_data)
            rendered += "\n"
            rendered += self._render_word_file_results(results)
            self._set_result(rendered)
            self.status_var.set("Đã chạy tìm kiếm theo WordFile.")
        except Exception as error:
            self.status_var.set("Không thể tìm theo WordFile.")
            messagebox.showerror("Lỗi", str(error))

    def run_phrase_search(self) -> None:
        try:
            index_data = self._require_index()
            phrase = self.phrase_var.get().strip()
            if not phrase:
                raise ValueError("Bạn cần nhập cụm từ cần tìm.")

            top_n = int(self.top_n_var.get().strip())
            finder = AdvancedQueryFinder(index_data)
            results = finder.FindPhrase(phrase, top_n)

            rendered = self._render_index_summary(index_data)
            rendered += "\n"
            rendered += self._render_phrase_results(results)
            self._set_result(rendered)
            self.status_var.set("Đã chạy tìm kiếm theo phrase query.")
        except Exception as error:
            self.status_var.set("Không thể tìm theo phrase query.")
            messagebox.showerror("Lỗi", str(error))

    def run_boolean_search(self) -> None:
        try:
            index_data = self._require_index()
            query = self.boolean_query_var.get().strip()
            if not query:
                raise ValueError("Bạn cần nhập boolean query.")

            finder = AdvancedQueryFinder(index_data)
            results = finder.FindBoolean(query)

            rendered = self._render_index_summary(index_data)
            rendered += "\n"
            rendered += self._render_boolean_results(results)
            self._set_result(rendered)
            self.status_var.set("Đã chạy tìm kiếm theo boolean query.")
        except Exception as error:
            self.status_var.set("Không thể tìm theo boolean query.")
            messagebox.showerror("Lỗi", str(error))

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = Chapter6DemoApp()
    app.run()


if __name__ == "__main__":
    main()
