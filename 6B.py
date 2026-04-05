import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import List


def _load_module(filename: str, module_name: str):
    module_path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Khong the nap module tu {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


module_6A = _load_module("6A.py", "module_6A")
InvertedIndexBuilder = module_6A.InvertedIndexBuilder
InvertedIndexData = module_6A.InvertedIndexData
normalize_search_token = module_6A.normalize_search_token
compute_tfidf_score = module_6A.compute_tfidf_score
print_summary = module_6A.print_summary


@dataclass(frozen=True)
class SearchResult:
    filename: str
    frequency: int
    score: float


class SingleWordFinder:
    def __init__(self, index_data: InvertedIndexData):
        self.index_data = index_data

    def Find(self, word: str, weight: int, top_n: int) -> List[SearchResult]:
        normalized = normalize_search_token(word, self.index_data.normalization_mode)
        postings = self.index_data.inverted_index.get(normalized, {})
        results = [
            SearchResult(
                filename=filename,
                frequency=frequency,
                score=compute_tfidf_score(self.index_data, filename, normalized, frequency, weight),
            )
            for filename, frequency in postings.items()
        ]
        results.sort(key=lambda item: (-item.score, item.filename))
        return results[:top_n]


def print_results(results: List[SearchResult]) -> None:
    if not results:
        print("Khong tim thay tai lieu phu hop.")
        return

    print("\n=== TOP DOCUMENTS ===")
    for index, result in enumerate(results, start=1):
        print(
            f"{index}. {result.filename} | tan suat = {result.frequency} | diem = {result.score:.4f}"
        )


def print_menu() -> None:
    print("\n===== FIND BY SINGLE WORD =====")
    print("1. Tao index va tim theo 1 tu")
    print("0. Thoat")


def main() -> None:
    builder = InvertedIndexBuilder()

    while True:
        print_menu()
        choice = input("Chon: ").strip()

        if choice == "1":
            directory = input("Nhap thu muc Dir: ").strip()
            stop_list = input("Nhap ten file StopList: ").strip()
            word = input("Nhap Word: ").strip()
            try:
                weight = int(input("Nhap Weight: ").strip())
                top_n = int(input("Nhap N: ").strip())
                index_data = builder.CreateIndex(directory, stop_list)
                finder = SingleWordFinder(index_data)
                print_summary(index_data)
                print_results(finder.Find(word, weight, top_n))
            except Exception as error:
                print("Loi:", error)

        elif choice == "0":
            print("Ket thuc chuong trinh.")
            break

        else:
            print("Lua chon khong hop le.")


if __name__ == "__main__":
    main()
