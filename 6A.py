import json
import math
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Set


WORD_PATTERN = re.compile(r"[^\W_]+", re.UNICODE)
IRREGULAR_LEMMAS = {
    "children": "child",
    "men": "man",
    "women": "woman",
    "mice": "mouse",
    "geese": "goose",
    "teeth": "tooth",
    "feet": "foot",
    "people": "person",
}


@dataclass(frozen=True)
class IndexedDocument:
    doc_id: int
    filename: str
    path: str
    token_count: int


@dataclass
class InvertedIndexData:
    directory: str
    stoplist_path: str
    normalization_mode: str
    doc_table: Dict[str, IndexedDocument]
    term_table: List[str]
    inverted_index: Dict[str, Dict[str, int]]
    doc_frequencies: Dict[str, int]
    document_count: int

    def to_json_ready(self) -> Dict[str, object]:
        return {
            "directory": self.directory,
            "stoplist_path": self.stoplist_path,
            "normalization_mode": self.normalization_mode,
            "doc_table": {
                filename: asdict(document)
                for filename, document in self.doc_table.items()
            },
            "term_table": self.term_table,
            "inverted_index": self.inverted_index,
            "doc_frequencies": self.doc_frequencies,
            "document_count": self.document_count,
        }


class InvertedIndexBuilder:
    def __init__(self, use_lemmatization: bool = False):
        self.use_lemmatization = use_lemmatization

    def set_lemmatization(self, enabled: bool) -> None:
        self.use_lemmatization = enabled

    def _normalize_token(self, token: str) -> str:
        normalized = unicodedata.normalize("NFKC", token).casefold()
        if not self.use_lemmatization:
            return normalized
        return lemmatize_token(normalized)

    def _load_stop_words(self, stoplist_path: Path) -> Set[str]:
        if not stoplist_path.exists():
            raise FileNotFoundError(f"Khong tim thay stop list: {stoplist_path}")

        stop_words: Set[str] = set()
        with stoplist_path.open("r", encoding="utf-8") as file:
            for line in file:
                for token in WORD_PATTERN.findall(line.lower()):
                    stop_words.add(self._normalize_token(token))
        return stop_words

    def _tokenize(self, text: str) -> List[str]:
        normalized_text = unicodedata.normalize("NFKC", text)
        return [self._normalize_token(token) for token in WORD_PATTERN.findall(normalized_text)]

    def CreateIndex(self, directory_name: str, stop_list_name: str) -> InvertedIndexData:
        directory = Path(directory_name).resolve()
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Thu muc khong hop le: {directory}")

        stoplist_path = directory / stop_list_name
        stop_words = self._load_stop_words(stoplist_path)

        doc_table: Dict[str, IndexedDocument] = {}
        inverted_index: Dict[str, Dict[str, int]] = {}
        doc_frequencies: Dict[str, int] = {}

        indexed_files = sorted(
            path for path in directory.iterdir() if path.is_file() and path.name != stop_list_name
        )

        for doc_id, filepath in enumerate(indexed_files, start=1):
            text = filepath.read_text(encoding="utf-8")
            tokens = self._tokenize(text)
            filtered_tokens = [token for token in tokens if token not in stop_words]

            doc_table[filepath.name] = IndexedDocument(
                doc_id=doc_id,
                filename=filepath.name,
                path=str(filepath),
                token_count=len(filtered_tokens),
            )

            seen_terms_in_doc: Set[str] = set()
            for token in filtered_tokens:
                postings = inverted_index.setdefault(token, {})
                postings[filepath.name] = postings.get(filepath.name, 0) + 1
                if token not in seen_terms_in_doc:
                    seen_terms_in_doc.add(token)
                    doc_frequencies[token] = doc_frequencies.get(token, 0) + 1

        term_table = sorted(inverted_index.keys())

        return InvertedIndexData(
            directory=str(directory),
            stoplist_path=str(stoplist_path),
            normalization_mode="lemma" if self.use_lemmatization else "exact",
            doc_table=doc_table,
            term_table=term_table,
            inverted_index=inverted_index,
            doc_frequencies=doc_frequencies,
            document_count=len(doc_table),
        )

    def save_index(self, index_data: InvertedIndexData, output_path: str) -> None:
        output = Path(output_path)
        output.write_text(
            json.dumps(index_data.to_json_ready(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def lemmatize_token(token: str) -> str:
    if not token:
        return token

    if token in IRREGULAR_LEMMAS:
        return IRREGULAR_LEMMAS[token]

    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"

    if len(token) > 4 and token.endswith("ves"):
        return token[:-3] + "f"

    if len(token) > 4 and token.endswith(("ches", "shes", "sses", "xes", "zes")):
        return token[:-2]

    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]

    return token


def normalize_search_token(token: str, normalization_mode: str) -> str:
    normalized = unicodedata.normalize("NFKC", token).casefold()
    if normalization_mode == "lemma":
        return lemmatize_token(normalized)
    return normalized


def tokenize_search_text(text: str, normalization_mode: str) -> List[str]:
    normalized_text = unicodedata.normalize("NFKC", text)
    return [
        normalize_search_token(token, normalization_mode)
        for token in WORD_PATTERN.findall(normalized_text)
    ]


def compute_tfidf_score(index_data: InvertedIndexData, filename: str, term: str, frequency: int, weight: int = 1) -> float:
    document = index_data.doc_table[filename]
    tf = frequency / max(document.token_count, 1)
    df = index_data.doc_frequencies.get(term, 0)
    idf = math.log((index_data.document_count + 1) / (df + 1)) + 1.0
    return tf * idf * weight


def print_summary(index_data: InvertedIndexData) -> None:
    print("\n=== DOC TABLE ===")
    for filename, document in sorted(index_data.doc_table.items()):
        print(f"{document.doc_id}. {filename}")

    print("\n=== TERM TABLE ===")
    if not index_data.term_table:
        print("Khong co term nao bat dau bang chu C/c.")
    else:
        for term in index_data.term_table:
            print(term)

    print("\n=== INVERTED INDEX ===")
    if not index_data.inverted_index:
        print("Inverted index rong.")
        return

    for term in index_data.term_table:
        postings = index_data.inverted_index[term]
        rendered = ", ".join(
            f"{filename}:{frequency}" for filename, frequency in sorted(postings.items())
        )
        print(f"{term} -> {rendered}")


def print_menu() -> None:
    print("\n===== CREATE INDEX =====")
    print("1. Tao inverted index")
    print("2. Tao inverted index va luu ra file JSON")
    print("0. Thoat")


def main() -> None:
    builder = InvertedIndexBuilder()

    while True:
        print_menu()
        choice = input("Chon: ").strip()

        if choice == "1":
            directory = input("Nhap thu muc Dir: ").strip()
            stop_list = input("Nhap ten file StopList: ").strip()
            try:
                index_data = builder.CreateIndex(directory, stop_list)
                print_summary(index_data)
            except Exception as error:
                print("Loi:", error)

        elif choice == "2":
            directory = input("Nhap thu muc Dir: ").strip()
            stop_list = input("Nhap ten file StopList: ").strip()
            output_path = input("Nhap file JSON dau ra: ").strip()
            try:
                index_data = builder.CreateIndex(directory, stop_list)
                builder.save_index(index_data, output_path)
                print_summary(index_data)
                print(f"\nDa luu index vao: {output_path}")
            except Exception as error:
                print("Loi:", error)

        elif choice == "0":
            print("Ket thuc chuong trinh.")
            break

        else:
            print("Lua chon khong hop le.")


if __name__ == "__main__":
    main()
