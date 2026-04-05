import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set


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
tokenize_search_text = module_6A.tokenize_search_text
compute_tfidf_score = module_6A.compute_tfidf_score
print_summary = module_6A.print_summary


@dataclass(frozen=True)
class MultiWordSearchResult:
    filename: str
    score: float
    matched_terms: Dict[str, int]


@dataclass(frozen=True)
class PhraseSearchResult:
    filename: str
    occurrences: int


@dataclass(frozen=True)
class BooleanSearchResult:
    filename: str


class WordFileFinder:
    def __init__(self, index_data: InvertedIndexData):
        self.index_data = index_data

    def _load_query_terms(self, word_file: str) -> List[tuple[str, int]]:
        query_path = Path(word_file)
        if not query_path.exists():
            raise FileNotFoundError(f"Khong tim thay WordFile: {query_path}")

        query_terms: List[tuple[str, int]] = []
        with query_path.open("r", encoding="utf-8-sig") as file:
            for line_no, line in enumerate(file, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                parts = stripped.split()
                if len(parts) != 2:
                    raise ValueError(
                        f"Dong {line_no} khong hop le. Dinh dang dung: <word> <weight>"
                    )
                word, raw_weight = parts
                normalized_word = normalize_search_token(word, self.index_data.normalization_mode)
                query_terms.append((normalized_word, int(raw_weight)))
        return query_terms

    def Find(self, word_file: str, top_n: int) -> List[MultiWordSearchResult]:
        query_terms = self._load_query_terms(word_file)
        scores: Dict[str, float] = {}
        matched_terms: Dict[str, Dict[str, int]] = {}

        for word, weight in query_terms:
            postings = self.index_data.inverted_index.get(word, {})
            for filename, frequency in postings.items():
                scores[filename] = scores.get(filename, 0.0) + compute_tfidf_score(
                    self.index_data,
                    filename,
                    word,
                    frequency,
                    weight,
                )
                matched_terms.setdefault(filename, {})[word] = frequency

        results = [
            MultiWordSearchResult(
                filename=filename,
                score=score,
                matched_terms=matched_terms.get(filename, {}),
            )
            for filename, score in scores.items()
        ]
        results.sort(key=lambda item: (-item.score, item.filename))
        return results[:top_n]


class AdvancedQueryFinder:
    def __init__(self, index_data: InvertedIndexData):
        self.index_data = index_data

    def _load_normalized_tokens(self, filename: str) -> List[str]:
        document = self.index_data.doc_table[filename]
        text = Path(document.path).read_text(encoding="utf-8")
        return tokenize_search_text(text, self.index_data.normalization_mode)

    def FindPhrase(self, phrase: str, top_n: int) -> List[PhraseSearchResult]:
        phrase_tokens = tokenize_search_text(phrase, self.index_data.normalization_mode)
        if not phrase_tokens:
            return []

        results: List[PhraseSearchResult] = []
        phrase_length = len(phrase_tokens)

        for filename in sorted(self.index_data.doc_table):
            tokens = self._load_normalized_tokens(filename)
            occurrences = 0
            for start_index in range(0, max(len(tokens) - phrase_length + 1, 0)):
                if tokens[start_index : start_index + phrase_length] == phrase_tokens:
                    occurrences += 1
            if occurrences > 0:
                results.append(PhraseSearchResult(filename=filename, occurrences=occurrences))

        results.sort(key=lambda item: (-item.occurrences, item.filename))
        return results[:top_n]

    def FindBoolean(self, query: str) -> List[BooleanSearchResult]:
        raw_tokens = query.replace("(", " ( ").replace(")", " ) ").split()
        if not raw_tokens:
            return []

        postfix = self._to_postfix(raw_tokens)
        universe = set(self.index_data.doc_table.keys())
        stack: List[Set[str]] = []

        for token in postfix:
            upper_token = token.upper()
            if upper_token == "AND":
                right = stack.pop()
                left = stack.pop()
                stack.append(left & right)
            elif upper_token == "OR":
                right = stack.pop()
                left = stack.pop()
                stack.append(left | right)
            elif upper_token == "NOT":
                operand = stack.pop()
                stack.append(universe - operand)
            else:
                normalized = normalize_search_token(token, self.index_data.normalization_mode)
                postings = self.index_data.inverted_index.get(normalized, {})
                stack.append(set(postings.keys()))

        if len(stack) != 1:
            raise ValueError("Boolean query không hợp lệ.")

        return [BooleanSearchResult(filename=name) for name in sorted(stack[0])]

    def _to_postfix(self, tokens: List[str]) -> List[str]:
        precedence = {"NOT": 3, "AND": 2, "OR": 1}
        output: List[str] = []
        operators: List[str] = []

        for token in tokens:
            upper_token = token.upper()
            if token == "(":
                operators.append(token)
            elif token == ")":
                while operators and operators[-1] != "(":
                    output.append(operators.pop())
                if not operators:
                    raise ValueError("Boolean query có ngoặc không khớp.")
                operators.pop()
            elif upper_token in precedence:
                while (
                    operators
                    and operators[-1] != "("
                    and precedence.get(operators[-1], 0) >= precedence[upper_token]
                ):
                    output.append(operators.pop())
                operators.append(upper_token)
            else:
                output.append(token)

        while operators:
            operator = operators.pop()
            if operator == "(":
                raise ValueError("Boolean query có ngoặc không khớp.")
            output.append(operator)

        return output


def print_results(results: List[MultiWordSearchResult]) -> None:
    if not results:
        print("Khong tim thay tai lieu phu hop.")
        return

    print("\n=== TOP DOCUMENTS ===")
    for index, result in enumerate(results, start=1):
        terms = ", ".join(
            f"{word}:{frequency}" for word, frequency in sorted(result.matched_terms.items())
        )
        print(f"{index}. {result.filename} | diem = {result.score:.4f} | terms = {terms}")


def print_phrase_results(results: List[PhraseSearchResult]) -> None:
    if not results:
        print("Khong tim thay tai lieu chua phrase phu hop.")
        return

    print("\n=== TOP DOCUMENTS BY PHRASE ===")
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.filename} | so lan xuat hien = {result.occurrences}")


def print_boolean_results(results: List[BooleanSearchResult]) -> None:
    if not results:
        print("Khong tim thay tai lieu phu hop voi boolean query.")
        return

    print("\n=== BOOLEAN QUERY RESULTS ===")
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.filename}")


def print_menu() -> None:
    print("\n===== FIND BY WORDFILE =====")
    print("1. Tao index va tim theo WordFile")
    print("0. Thoat")


def main() -> None:
    builder = InvertedIndexBuilder()

    while True:
        print_menu()
        choice = input("Chon: ").strip()

        if choice == "1":
            directory = input("Nhap thu muc Dir: ").strip()
            stop_list = input("Nhap ten file StopList: ").strip()
            word_file = input("Nhap duong dan WordFile: ").strip()
            try:
                top_n = int(input("Nhap N: ").strip())
                index_data = builder.CreateIndex(directory, stop_list)
                finder = WordFileFinder(index_data)
                print_summary(index_data)
                print_results(finder.Find(word_file, top_n))
            except Exception as error:
                print("Loi:", error)

        elif choice == "0":
            print("Ket thuc chuong trinh.")
            break

        else:
            print("Lua chon khong hop le.")


if __name__ == "__main__":
    main()
