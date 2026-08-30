import asyncio
from collections import OrderedDict
from pathlib import Path

import pytest

from cogs.faq import FAQ, FEEDBACK_MEMORY, FAQTopicSelect
from core.faq import (
    FAQ_DIR,
    FaqDefinitionError,
    FaqMatcher,
    load_topics,
    parse_topic,
)
from helpers.faq import FEEDBACK_NOTE, HELPFUL, UNHELPFUL, send_faq_embed
from tests.conftest import (
    FakeBot,
    FakeChannel,
    FakeInteraction,
    FakeMessage,
    FakeReactionPayload,
)

WAITING = """\
+++
title = "Waiting Time"
threshold = 2.0
cooldown = 60
triggers = ["ventetid", "wait", "waiting", "time", "training"]
phrases = ["how long"]

[weights]
"how long" = 1.5
"time" = 0.3
"training" = 0.5
"ventetid" = 2.0
+++
It varies by country.
"""

APPLICATION = """\
+++
title = "ATC Application"
threshold = 2.0
triggers = ["apply", "atc", "train", "trained", "training"]
phrases = ["become a controller"]
exclude = ["pilot"]

[weights]
"train" = 0.5
"trained" = 0.5
"training" = 0.5
+++
Start in the Control Center.
"""


@pytest.fixture
def topics(tmp_path: Path) -> Path:
    (tmp_path / 'application.md').write_text(APPLICATION, encoding='utf8')
    (tmp_path / 'waiting.md').write_text(WAITING, encoding='utf8')
    return tmp_path


@pytest.fixture
def matcher(topics: Path) -> FaqMatcher:
    return FaqMatcher(load_topics(topics))


def test_a_topic_file_reads_into_its_parts(topics: Path) -> None:
    topic = parse_topic(topics / 'waiting.md')

    assert topic.title == 'Waiting Time'
    assert topic.threshold == 2.0
    assert topic.cooldown == 60
    assert topic.answer == 'It varies by country.'


def test_an_unweighted_trigger_is_worth_one(topics: Path) -> None:
    topic = parse_topic(topics / 'waiting.md')

    assert topic.triggers['wait'] == 1.0
    assert topic.triggers['ventetid'] == 2.0


def test_an_unweighted_phrase_is_worth_more_than_a_word(topics: Path) -> None:
    topic = parse_topic(topics / 'application.md')

    assert topic.phrases['become a controller'] == 2.0


def test_a_file_without_frontmatter_is_rejected(tmp_path: Path) -> None:
    broken = tmp_path / 'broken.md'
    broken.write_text('Just an answer, no frontmatter.', encoding='utf8')

    with pytest.raises(FaqDefinitionError):
        parse_topic(broken)


def test_a_file_without_an_answer_is_rejected(tmp_path: Path) -> None:
    empty = tmp_path / 'empty.md'
    empty.write_text('+++\ntitle = "X"\ntriggers = ["x"]\n+++\n', encoding='utf8')

    with pytest.raises(FaqDefinitionError):
        parse_topic(empty)


def test_one_broken_file_does_not_cost_us_the_others(topics: Path) -> None:
    (topics / 'broken.md').write_text('+++\nnot toml\n+++\nanswer', encoding='utf8')

    assert sorted(load_topics(topics)) == ['ATC Application', 'Waiting Time']


def test_triggers_match_on_the_word_stem(matcher: FaqMatcher) -> None:
    # 'ventetiden' is 'ventetid' with the Danish article stuck on the end.
    assert matcher.rank('hvad er ventetiden?') == ['Waiting Time']


def test_a_word_counts_once_however_it_is_spelled_in_the_triggers(
    matcher: FaqMatcher,
) -> None:
    # 'training' matches train, trained and training, but says one thing.
    assert matcher.score('training')['ATC Application'] == 0.5


def test_a_phrase_counts_on_top_of_the_words_in_it(matcher: FaqMatcher) -> None:
    # 'how long' is 1.5, 'training' another 0.5.
    assert matcher.score('how long is training?')['Waiting Time'] == 2.0


def test_a_topic_below_its_threshold_is_not_offered(matcher: FaqMatcher) -> None:
    assert matcher.rank('how long have you been flying?') == []


def test_an_excluded_word_rules_a_topic_out(matcher: FaqMatcher) -> None:
    assert 'ATC Application' in matcher.rank('how do I apply for atc training?')
    assert 'ATC Application' not in matcher.rank(
        'how do I apply for atc training as a pilot?'
    )


def test_the_best_match_wins_over_file_order(matcher: FaqMatcher) -> None:
    # 'ATC Application' sorts first, but this is a question about waiting.
    assert matcher.rank('how long does atc training take?')[0] == 'Waiting Time'


def test_every_shipped_topic_parses() -> None:
    files = sorted(FAQ_DIR.glob('*.md'))

    assert files
    assert len(load_topics(FAQ_DIR)) == len(files)


def build(topics: Path) -> FAQ:
    """The cog without Discord, answering from the test topics."""
    cog = FAQ.__new__(FAQ)
    cog.topics = load_topics(topics)
    cog.matcher = FaqMatcher(cog.topics)
    cog.recent_replies = {}
    cog.answered = OrderedDict()
    return cog


def test_the_bot_answers_a_question_it_recognises(topics: Path) -> None:
    channel = FakeChannel()

    asyncio.run(build(topics).on_message(FakeMessage('how long is the wait?', channel)))

    content, _ = channel.sent[0]
    assert 'Waiting Time' in content


def test_a_topic_on_cooldown_does_not_silence_the_others(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()

    asyncio.run(cog.on_message(FakeMessage('how long is the wait?', channel)))
    asyncio.run(cog.on_message(FakeMessage('how do I apply for atc?', channel)))

    assert len(channel.sent) == 2
    assert 'Waiting Time' in channel.sent[0][0]
    assert 'ATC Application' in channel.sent[1][0]


def test_the_same_topic_stays_quiet_while_on_cooldown(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()

    asyncio.run(cog.on_message(FakeMessage('how do I apply for atc?', channel)))
    asyncio.run(cog.on_message(FakeMessage('where do I apply for atc?', channel)))

    assert len(channel.sent) == 1


def test_the_cooldown_is_per_channel(topics: Path) -> None:
    cog = build(topics)
    first, second = FakeChannel(1), FakeChannel(2)

    asyncio.run(cog.on_message(FakeMessage('how do I apply for atc?', first)))
    asyncio.run(cog.on_message(FakeMessage('how do I apply for atc?', second)))

    assert len(first.sent) == 1
    assert len(second.sent) == 1


def test_picking_a_topic_replies_to_the_message_that_asked(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()
    asked = FakeMessage('any idea about this?', channel)
    interaction = FakeInteraction()

    select = FAQTopicSelect(cog, asked, list(cog.topics))
    select._values = ['Waiting Time']
    asyncio.run(select.callback(interaction))

    content, _ = channel.sent[0]
    assert channel.replied_to == [asked]
    assert '@tester' in content
    assert "I believe you're asking about" not in content
    assert interaction.response.edits == ['Replied with **Waiting Time**.']


def test_a_manual_answer_puts_the_topic_on_cooldown(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()
    asked = FakeMessage('any idea about this?', channel)

    select = FAQTopicSelect(cog, asked, list(cog.topics))
    select._values = ['Waiting Time']
    asyncio.run(select.callback(FakeInteraction()))

    asyncio.run(cog.on_message(FakeMessage('how long is the wait?', channel)))

    assert len(channel.sent) == 1


def test_a_second_pick_does_not_answer_twice(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()
    asked = FakeMessage('any idea about this?', channel)

    select = FAQTopicSelect(cog, asked, list(cog.topics))
    select._values = ['Waiting Time']
    asyncio.run(select.callback(FakeInteraction()))
    asyncio.run(select.callback(FakeInteraction()))

    assert len(channel.sent) == 1


def test_a_reply_the_channel_refuses_leaves_no_cooldown(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()
    channel.refuse_send = True
    asked = FakeMessage('any idea about this?', channel)
    interaction = FakeInteraction()

    select = FAQTopicSelect(cog, asked, list(cog.topics))
    select._values = ['Waiting Time']
    asyncio.run(select.callback(interaction))

    # Nothing was posted, so the topic must be free to answer on its own.
    assert cog.recent_replies == {}
    assert interaction.response.messages
    assert not interaction.response.edits


def test_a_refused_reply_can_be_tried_again(topics: Path) -> None:
    cog = build(topics)
    channel = FakeChannel()
    channel.refuse_send = True
    asked = FakeMessage('any idea about this?', channel)

    select = FAQTopicSelect(cog, asked, list(cog.topics))
    select._values = ['Waiting Time']
    asyncio.run(select.callback(FakeInteraction()))

    channel.refuse_send = False
    asyncio.run(select.callback(FakeInteraction()))

    assert len(channel.sent) == 1


def test_an_answer_offers_the_feedback_reactions(topics: Path) -> None:
    channel = FakeChannel()

    asyncio.run(build(topics).on_message(FakeMessage('how long is the wait?', channel)))

    _, embed = channel.sent[0]
    assert embed.footer.text == FEEDBACK_NOTE
    assert channel.posted[0].reactions == [HELPFUL, UNHELPFUL]


def test_an_answer_still_posts_when_the_reactions_are_refused(topics: Path) -> None:
    channel = FakeChannel()
    channel.refuse_reactions = True

    asyncio.run(build(topics).on_message(FakeMessage('how long is the wait?', channel)))

    assert len(channel.sent) == 1


def test_an_answer_is_remembered_before_the_reactions_go_on(topics: Path) -> None:
    channel = FakeChannel()
    reactions_when_remembered: list[list[str]] = []

    asyncio.run(
        send_faq_embed(
            channel,
            '@tester',
            'Waiting Time',
            'It varies by country.',
            remember=lambda posted: reactions_when_remembered.append(
                list(posted.reactions)
            ),
        )
    )

    # A vote can land the moment our own first reaction does, so nothing may be
    # on the answer yet by the time it is remembered.
    assert reactions_when_remembered == [[]]
    assert channel.posted[0].reactions == [HELPFUL, UNHELPFUL]


def test_a_refused_thumbs_up_still_offers_the_thumbs_down(topics: Path) -> None:
    channel = FakeChannel()
    channel.refused_reactions = [HELPFUL]

    asyncio.run(build(topics).on_message(FakeMessage('how long is the wait?', channel)))

    assert channel.posted[0].reactions == [UNHELPFUL]


def test_a_vote_on_an_answer_is_recorded(topics: Path) -> None:
    cog = build(topics)
    cog.bot = FakeBot(None)
    cog.remember_answer(77, 'Waiting Time')

    assert cog.record_feedback(FakeReactionPayload(1, 42, 77, HELPFUL))


def test_a_vote_on_anything_else_is_ignored(topics: Path) -> None:
    cog = build(topics)
    cog.bot = FakeBot(None)
    cog.remember_answer(77, 'Waiting Time')

    assert not cog.record_feedback(FakeReactionPayload(1, 42, 78, HELPFUL))
    assert not cog.record_feedback(FakeReactionPayload(1, 42, 77, '⭐'))


def test_the_bot_forgets_the_oldest_answers(topics: Path) -> None:
    cog = build(topics)

    for message_id in range(FEEDBACK_MEMORY + 10):
        cog.remember_answer(message_id, 'Waiting Time')

    assert len(cog.answered) == FEEDBACK_MEMORY
    assert 0 not in cog.answered
