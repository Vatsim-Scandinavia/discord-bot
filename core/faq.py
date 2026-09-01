"""
The FAQ topics the bot answers with, and the matching that picks one.

Each topic is one Markdown file in ``messages/faq/``: a TOML frontmatter block
describing when it applies, then the answer itself. Adding or retuning an FAQ is
a change to that one file, no code involved.

Matching is deliberately plain. Words in the message are stemmed and looked up
against the triggers, phrases are matched literally, and the weights add up to a
score the topic's threshold has to clear. Nothing here needs a model or a
network call.
"""

import re
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import snowballstemmer
import structlog

from core.exceptions import ExpectedMixin

logger = structlog.stdlib.get_logger()

FAQ_DIR = Path('messages/faq')

FRONTMATTER = re.compile(
    r'\A\+\+\+[^\S\n]*\n(?P<meta>.*?)\n\+\+\+[^\S\n]*\n(?P<answer>.*)\Z', re.DOTALL
)
WORD = re.compile(r'\b\w+\b')

DEFAULT_TRIGGER_WEIGHT = 1.0
DEFAULT_PHRASE_WEIGHT = 2.0
DEFAULT_COOLDOWN = 3600

# Snowball has no Icelandic stemmer, so Icelandic triggers match on the exact
# word. Everything a trigger is written as still matches itself regardless.
STEMMED_LANGUAGES = ('english', 'danish', 'norwegian', 'swedish', 'finnish')

_STEMMERS = {
    language: snowballstemmer.stemmer(language) for language in STEMMED_LANGUAGES
}


class FaqDefinitionError(Exception, ExpectedMixin):
    """Raised when an FAQ file cannot be read as a topic."""

    def __init__(self, path: Path, problem: str):
        super().__init__()
        self.path = path
        self.problem = problem

    def __str__(self):
        """Return a string representation of the exception."""
        return f'{self.path} is not a usable FAQ topic: {self.problem}'


@lru_cache(maxsize=4096)
def stem_keys(word: str) -> frozenset[str]:
    """
    Return every form of a word that may be matched on.

    Keys carry their language, so the Danish stem of one word cannot collide
    with the Finnish stem of another.
    """
    word = word.lower()
    keys = {f'raw:{word}'}
    keys.update(
        f'{language}:{stemmer.stemWord(word)}'
        for language, stemmer in _STEMMERS.items()
    )

    return frozenset(keys)


@dataclass(frozen=True)
class FaqTopic:
    """One answer, and what a message has to look like to earn it."""

    title: str
    answer: str
    threshold: float
    cooldown: int
    triggers: dict[str, float]
    phrases: dict[str, float]
    exclude: frozenset[str]


def _weigh(names: list[str], overrides: dict[str, float], default: float):
    """Pair every trigger or phrase with its weight, the authored one if given."""
    return {
        name.lower(): float(overrides.get(name, default))
        for name in names
        if name.strip()
    }


def parse_topic(path: Path) -> FaqTopic:
    """Read one Markdown file into a topic. Raises on anything malformed."""
    match = FRONTMATTER.match(path.read_text(encoding='utf8'))
    if not match:
        raise FaqDefinitionError(path, 'no +++ frontmatter block at the top')

    try:
        meta = tomllib.loads(match['meta'])
    except tomllib.TOMLDecodeError as error:
        raise FaqDefinitionError(path, f'invalid TOML: {error}') from error

    title = meta.get('title')
    if not title:
        raise FaqDefinitionError(path, 'no title')

    answer = match['answer'].strip()
    if not answer:
        raise FaqDefinitionError(path, 'no answer below the frontmatter')

    weights = meta.get('weights', {})
    triggers = _weigh(meta.get('triggers', []), weights, DEFAULT_TRIGGER_WEIGHT)
    phrases = _weigh(meta.get('phrases', []), weights, DEFAULT_PHRASE_WEIGHT)

    if not triggers and not phrases:
        raise FaqDefinitionError(path, 'no triggers and no phrases')

    return FaqTopic(
        title=title,
        answer=answer,
        threshold=float(meta.get('threshold', DEFAULT_TRIGGER_WEIGHT)),
        cooldown=int(meta.get('cooldown', DEFAULT_COOLDOWN)),
        triggers=triggers,
        phrases=phrases,
        exclude=frozenset(word.lower() for word in meta.get('exclude', [])),
    )


def load_topics(folder: Path = FAQ_DIR) -> dict[str, FaqTopic]:
    """
    Read every topic in a folder, in filename order.

    A file that cannot be read is logged and skipped rather than taking the cog
    down with it, so a typo in one FAQ never costs us the others.
    """
    topics: dict[str, FaqTopic] = {}

    for path in sorted(folder.glob('*.md')):
        try:
            topic = parse_topic(path)
        except FaqDefinitionError as error:
            # The error says what is wrong with the file and where; a traceback
            # through the parser would only bury that.
            logger.error(  # noqa: TRY400
                'Skipping FAQ topic', path=str(path), problem=error.problem
            )
            continue
        except OSError:
            logger.exception('Could not read FAQ topic', path=str(path))
            continue

        topics[topic.title] = topic

    logger.info('Loaded FAQ topics', count=len(topics), titles=list(topics))

    return topics


class FaqMatcher:
    """Scores a message against the loaded topics."""

    def __init__(self, topics: dict[str, FaqTopic]):
        self.topics = topics
        self._index = self._build_index(topics)

    @staticmethod
    def _build_index(
        topics: dict[str, FaqTopic],
    ) -> dict[str, set[tuple[str, str]]]:
        """Map every stem of every trigger to the topics that claim it."""
        index: dict[str, set[tuple[str, str]]] = defaultdict(set)

        for title, topic in topics.items():
            for trigger in topic.triggers:
                for key in stem_keys(trigger):
                    index[key].add((title, trigger))

        return index

    def score(self, content: str) -> dict[str, float]:
        """Score every topic against a message, whether or not it qualifies."""
        text = content.lower()
        words = WORD.findall(text)

        # Each word is worth the best trigger it matches, counted once. A topic
        # listing "train", "training" and "trained" separately describes one
        # idea three ways, and one word saying it should not score three times.
        best: dict[str, dict[str, float]] = defaultdict(dict)
        for word in set(words):
            for key in stem_keys(word):
                for title, trigger in self._index.get(key, ()):
                    weight = self.topics[title].triggers[trigger]
                    if weight > best[title].get(word, 0.0):
                        best[title][word] = weight

        scores: dict[str, float] = {}
        for title, topic in self.topics.items():
            if any(word in topic.exclude for word in words):
                continue

            score = sum(best[title].values()) if title in best else 0.0
            score += sum(
                weight for phrase, weight in topic.phrases.items() if phrase in text
            )
            scores[title] = score

        return scores

    def rank(self, content: str) -> list[str]:
        """Return the topics a message earns, best match first."""
        scored = [
            (score, title)
            for title, score in self.score(content).items()
            if score >= self.topics[title].threshold
        ]

        # Stable, so topics scoring the same stay in file order.
        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [title for _, title in scored]
