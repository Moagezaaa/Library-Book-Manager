import sqlite3
import os
from typing import List

from models.book import Book

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")


class BookStore:
    def __init__(self) -> None:
        self._conn = sqlite3.connect(DB_PATH)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._create_table()
        if not self.get_all_books():
            self._seed_data()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                book_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                author      TEXT    NOT NULL,
                year        INTEGER NOT NULL,
                is_borrowed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def _seed_data(self) -> None:
        self.add_book("Clean Code", "Robert C. Martin", 2008)
        self.add_book("The Pragmatic Programmer", "Andrew Hunt", 1999)
        self.add_book("Design Patterns", "Erich Gamma", 1994)

    def add_book(self, title: str, author: str, year: int) -> Book:
        cur = self._conn.execute(
            "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
            (title.strip(), author.strip(), year),
        )
        self._conn.commit()
        return Book(
            book_id=cur.lastrowid,
            title=title.strip(),
            author=author.strip(),
            year=year,
        )

    def get_all_books(self) -> List[Book]:
        rows = self._conn.execute("SELECT book_id, title, author, year, is_borrowed FROM books").fetchall()
        return [Book(*row[:-1], is_borrowed=bool(row[-1])) for row in rows]

    def search_books(self, keyword: str) -> List[Book]:
        normalized = keyword.strip().lower()
        if not normalized:
            return self.get_all_books()
        pattern = f"%{normalized}%"
        rows = self._conn.execute(
            "SELECT book_id, title, author, year, is_borrowed FROM books "
            "WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?",
            (pattern, pattern),
        ).fetchall()
        return [Book(*row[:-1], is_borrowed=bool(row[-1])) for row in rows]

    def borrow_book(self, book_id: int) -> bool:
        cur = self._conn.execute(
            "UPDATE books SET is_borrowed = 1 WHERE book_id = ? AND is_borrowed = 0",
            (book_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def return_book(self, book_id: int) -> bool:
        cur = self._conn.execute(
            "UPDATE books SET is_borrowed = 0 WHERE book_id = ? AND is_borrowed = 1",
            (book_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def delete_book(self, book_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def get_book_by_id(self, book_id: int) -> Book | None:
        row = self._conn.execute(
            "SELECT book_id, title, author, year, is_borrowed FROM books WHERE book_id = ?",
            (book_id,),
        ).fetchone()
        if row is None:
            return None
        return Book(*row[:-1], is_borrowed=bool(row[-1]))

    def get_stats(self) -> dict[str, int]:
        row = self._conn.execute(
            "SELECT COUNT(*), SUM(is_borrowed) FROM books"
        ).fetchone()
        total = row[0]
        borrowed = row[1] or 0
        return {
            "total": total,
            "borrowed": borrowed,
            "available": total - borrowed,
        }
