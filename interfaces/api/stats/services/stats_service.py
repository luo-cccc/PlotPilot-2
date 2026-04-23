"""Statistics service layer for business logic."""
from typing import Optional, List, Dict
from datetime import datetime
import logging

from ..repositories.stats_repository import StatsRepository
from ..models.stats_models import GlobalStats, BookStats, ChapterStats, WritingProgress

logger = logging.getLogger(__name__)


class StatsService:
    """Service layer for statistics business logic.

    This class provides high-level methods for calculating statistics across
    books, chapters, and tracking writing progress. It coordinates between the
    repository layer (data access) and models (data structures).
    """

    def __init__(self, repository: StatsRepository):
        """Initialize the service with a repository.

        Args:
            repository: StatsRepository instance for data access
        """
        self.repository = repository
        logger.info("StatsService initialized")

    def get_global_stats(self) -> GlobalStats:
        """Get global statistics across all books.

        Iterates through all books and aggregates totals:
        - Total books count
        - Total chapters across all books
        - Total word count
        - Total character count
        - Books categorized by stage

        Returns:
            GlobalStats object with aggregated data
        """
        logger.info("Calculating global statistics")

        book_slugs = self.repository.get_all_book_slugs()
        total_books = len(book_slugs)
        total_chapters = 0
        total_words = 0
        total_characters = 0
        books_by_stage: Dict[str, int] = {}

        for slug in book_slugs:
            manifest = self.repository.get_book_manifest(slug)
            if manifest:
                stage = manifest.get("stage", "unknown")
                books_by_stage[stage] = books_by_stage.get(stage, 0) + 1

            outline = self.repository.get_book_outline(slug)
            if outline and "chapters" in outline:
                total_chapters += len(outline["chapters"])

                # Calculate words and characters for this book
                for chapter_info in outline["chapters"]:
                    chapter_id = chapter_info.get("id")
                    if chapter_id:
                        content = self.repository.get_chapter_content(slug, chapter_id)
                        if content:
                            word_count = self.repository.count_words(content)
                            total_words += word_count
                            total_characters += len(content)

        stats = GlobalStats(
            total_books=total_books,
            total_chapters=total_chapters,
            total_words=total_words,
            total_characters=total_characters,
            books_by_stage=books_by_stage
        )

        logger.info(f"Global stats: {total_books} books, {total_chapters} chapters, {total_words} words")
        return stats

    def get_book_stats(self, slug: str) -> Optional[BookStats]:
        """Get statistics for a specific book.

        Calculates:
        - Total chapter count from outline
        - Completed chapters (those with content)
        - Total word count across all chapters
        - Average words per chapter
        - Completion rate (completed / total)

        Args:
            slug: The book's slug (directory name)

        Returns:
            BookStats object if book found, None otherwise
        """
        logger.info(f"Getting book statistics for: {slug}")

        manifest = self.repository.get_book_manifest(slug)
        if not manifest:
            logger.warning(f"Book not found: {slug}")
            return None

        title = manifest.get("title", slug)

        outline = self.repository.get_book_outline(slug)
        if not outline or "chapters" not in outline:
            logger.warning(f"Outline not found or invalid for book: {slug}")
            return None

        chapters_info = outline["chapters"]
        total_chapters = len(chapters_info)
        completed_chapters = 0
        total_words = 0

        for chapter_info in chapters_info:
            chapter_id = chapter_info.get("id")
            if chapter_id:
                content = self.repository.get_chapter_content(slug, chapter_id)
                if content:
                    word_count = self.repository.count_words(content)
                    if word_count > 0:
                        completed_chapters += 1
                    total_words += word_count

        avg_chapter_words = total_words // total_chapters if total_chapters > 0 else 0
        completion_rate = completed_chapters / total_chapters if total_chapters > 0 else 0.0

        stats = BookStats(
            slug=slug,
            title=title,
            total_chapters=total_chapters,
            completed_chapters=completed_chapters,
            total_words=total_words,
            avg_chapter_words=avg_chapter_words,
            completion_rate=completion_rate,
            last_updated=datetime.now()
        )

        logger.info(f"Book stats for {slug}: {total_chapters} chapters, {completed_chapters} completed, {total_words} words")
        return stats

    def get_chapter_stats(self, slug: str, chapter_id: int) -> Optional[ChapterStats]:
        """Get statistics for a specific chapter.

        Finds the chapter title from outline and calculates:
        - Word count (supporting mixed Chinese/English)
        - Character count
        - Paragraph count
        - Whether content exists

        Args:
            slug: The book's slug (directory name)
            chapter_id: The chapter's numeric ID (>= 1)

        Returns:
            ChapterStats object if chapter found, None otherwise
        """
        logger.info(f"Getting chapter statistics for: {slug}, chapter {chapter_id}")

        outline = self.repository.get_book_outline(slug)
        if not outline or "chapters" not in outline:
            logger.warning(f"Outline not found or invalid for book: {slug}")
            return None

        # Find chapter title from outline
        chapter_title = f"Chapter {chapter_id}"
        for chapter_info in outline["chapters"]:
            if chapter_info.get("id") == chapter_id:
                chapter_title = chapter_info.get("title", chapter_title)
                break

        content = self.repository.get_chapter_content(slug, chapter_id)
        if content is None:
            logger.warning(f"Chapter content not found: {slug}, chapter {chapter_id}")
            return None

        # Calculate statistics
        word_count = self.repository.count_words(content)
        character_count = len(content)

        # Count paragraphs (non-empty lines)
        lines = content.split('\n')
        paragraph_count = sum(1 for line in lines if line.strip())

        has_content = word_count > 0 or character_count > 0

        stats = ChapterStats(
            chapter_id=chapter_id,
            title=chapter_title,
            word_count=word_count,
            character_count=character_count,
            paragraph_count=paragraph_count,
            has_content=has_content
        )

        logger.info(f"Chapter stats for {slug}/{chapter_id}: {word_count} words, {character_count} chars, {paragraph_count} paragraphs")
        return stats

    def get_writing_progress(self, slug: str, days: int = 30) -> List[WritingProgress]:
        """Get writing progress over time.

        基于文件系统统计每日写作进度：
        - 遍历 outline 中的章节
        - 读取 body.md 的字数和修改时间
        - 按日期聚合每日字数和完成章节数

        Args:
            slug: The book's slug (directory name)
            days: Number of days to look back (default 30)

        Returns:
            List of WritingProgress objects for the last N days
        """
        from collections import defaultdict
        import os
        from pathlib import Path

        logger.info(f"Getting writing progress for: {slug}, days={days}")

        outline = self.repository.get_book_outline(slug)
        if not outline or "chapters" not in outline:
            return []

        daily_progress: dict[str, dict[str, int]] = defaultdict(lambda: {"words": 0, "chapters": 0})

        for chapter_info in outline["chapters"]:
            chapter_id = chapter_info.get("id")
            if not chapter_id:
                continue
            chapter_path = self.repository.books_root / slug / "chapters" / f"ch-{chapter_id:04d}" / "body.md"
            if not chapter_path.exists():
                continue
            content = self.repository.get_chapter_content(slug, chapter_id)
            if not content:
                continue
            word_count = self.repository.count_words(content)
            if word_count <= 0:
                continue
            mtime = os.path.getmtime(chapter_path)
            date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
            daily_progress[date_str]["words"] += word_count
            daily_progress[date_str]["chapters"] += 1

        # 限制返回最近 N 天
        cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
        result = []
        for date_str in sorted(daily_progress.keys()):
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt >= cutoff:
                result.append(WritingProgress(
                    date=dt,
                    words_written=daily_progress[date_str]["words"],
                    chapters_completed=daily_progress[date_str]["chapters"],
                ))

        logger.info(f"Writing progress for {slug}: {len(result)} days of data")
        return result
