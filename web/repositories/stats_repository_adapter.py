"""Statistics repository adapter for new DDD architecture.

This adapter bridges the gap between the legacy stats API (which expects
manifest.json files and slug-based identifiers) and the new DDD architecture
(which uses JSON files with UUID-based identifiers).
"""
from pathlib import Path
from typing import Optional, Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class StatsRepositoryAdapter:
    """Adapter to make new architecture data compatible with stats API.

    This adapter:
    1. Reads from data/novels/*.json instead of data/{slug}/manifest.json
    2. Converts novel-id to slug for API compatibility
    3. Extracts chapter data from the novel JSON structure
    """

    def __init__(self, data_root: Path):
        """Initialize the adapter with data root path.

        Args:
            data_root: Path to the data directory (contains novels/ and bibles/)
        """
        self.data_root = Path(data_root)
        self.novels_dir = self.data_root / "novels"
        logger.info(f"StatsRepositoryAdapter initialized with data_root: {self.data_root}")

    def get_all_book_slugs(self) -> List[str]:
        """Get all book slugs (novel IDs) by scanning novels directory.

        Returns:
            List of novel IDs that can be used as slugs
        """
        slugs = []
        try:
            if not self.novels_dir.exists():
                logger.warning(f"Novels directory does not exist: {self.novels_dir}")
                return slugs

            for novel_file in self.novels_dir.glob("*.json"):
                # Use the filename (without .json) as the slug
                slug = novel_file.stem
                slugs.append(slug)
            logger.info(f"Found {len(slugs)} novels: {slugs}")
        except Exception as e:
            logger.error(f"Error scanning novels directory: {e}")
        return slugs

    def get_book_manifest(self, slug: str) -> Optional[Dict]:
        """Read a novel's data and convert to manifest format.

        Args:
            slug: The novel's ID (used as slug)

        Returns:
            Dictionary in manifest format, or None if not found/error
        """
        try:
            novel_path = self.novels_dir / f"{slug}.json"
            if not novel_path.exists():
                logger.warning(f"Novel not found: {slug}")
                return None

            with open(novel_path, 'r', encoding='utf-8') as f:
                novel_data = json.load(f)

            # Convert new format to legacy manifest format
            manifest = {
                "title": novel_data.get("title", ""),
                "author": novel_data.get("author", ""),
                "slug": slug,
                "stage": novel_data.get("stage", "planning"),
                "target_chapters": novel_data.get("target_chapters", 0),
                "chapters": novel_data.get("chapters", [])
            }

            logger.debug(f"Successfully read manifest for novel: {slug}")
            return manifest
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in novel file {slug}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading novel {slug}: {e}")
            return None

    def get_book_outline(self, slug: str) -> Optional[Dict]:
        """Read a novel's outline data.

        Note: In the new architecture, outline data might be stored differently.
        For now, return None as outlines are not yet implemented.

        Args:
            slug: The novel's ID (used as slug)

        Returns:
            Dictionary containing outline data, or None
        """
        logger.debug(f"Outline requested for {slug} - not yet implemented in new architecture")
        return None

    def get_chapter_content(self, slug: str, chapter_id: int) -> Optional[str]:
        """Read a chapter's content from the novel data.

        Args:
            slug: The novel's ID (used as slug)
            chapter_id: The chapter's numeric ID (>= 1)

        Returns:
            String containing chapter content, or None if not found/error
        """
        try:
            manifest = self.get_book_manifest(slug)
            if not manifest:
                return None

            chapters = manifest.get("chapters", [])

            # Find chapter by ID
            for chapter in chapters:
                if chapter.get("number") == chapter_id:
                    content = chapter.get("content", "")
                    logger.debug(f"Successfully read chapter {chapter_id} for novel: {slug}")
                    return content

            logger.warning(f"Chapter {chapter_id} not found in novel {slug}")
            return None
        except Exception as e:
            logger.error(f"Error reading chapter {chapter_id} for novel {slug}: {e}")
            return None

    def count_words(self, text: str) -> int:
        """Count words in text, supporting both Chinese and English.

        Chinese characters are counted individually (each character = 1 word).
        English words are counted using whitespace separation.

        Args:
            text: The text to analyze

        Returns:
            Total word count (Chinese characters + English words)
        """
        if not text or not text.strip():
            return 0

        import re

        # Count Chinese characters (including CJK Unified Ideographs and Extension blocks)
        chinese_pattern = r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf]'
        chinese_chars = len(re.findall(chinese_pattern, text))

        # Count English words (ASCII letters sequences)
        # Remove Chinese text first to avoid double-counting
        english_text = re.sub(chinese_pattern, '', text)
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', english_text))

        total_words = chinese_chars + english_words
        logger.debug(f"Word count: {total_words} (Chinese: {chinese_chars}, English: {english_words})")
        return total_words
