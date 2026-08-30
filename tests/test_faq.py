import pytest

from cogs.faq import FAQ

TRIGGERS = {
    'ATC Application': {'triggers': {'apply', 'atc', 'training'}, 'threshold': 2},
    'Waiting Time': {'triggers': {'wait', 'time', 'training'}, 'threshold': 2},
}


@pytest.fixture
def cog() -> FAQ:
    """Build the cog without touching Discord or the message files."""
    cog = FAQ.__new__(FAQ)
    cog.faq_triggers = TRIGGERS
    cog.trigger_weights = FAQ._build_trigger_weights(TRIGGERS)
    return cog


def test_shared_triggers_count_for_less_than_unique_ones(cog: FAQ) -> None:
    assert cog.trigger_weights['training'] == 0.5
    assert cog.trigger_weights['atc'] == 1.0


def test_best_match_wins_over_definition_order(cog: FAQ) -> None:
    # Both topics qualify, but 'ATC Application' is defined first and used to
    # win on that alone. Waiting matches wait + time + training, ATC only
    # atc + training, so waiting is the better answer.
    assert cog.rank_topics('atc training, how long is the wait time?') == [
        'Waiting Time',
        'ATC Application',
    ]


def test_topic_below_its_threshold_does_not_qualify(cog: FAQ) -> None:
    assert cog.rank_topics('is training fun?') == []


def test_message_without_any_trigger_ranks_nothing(cog: FAQ) -> None:
    assert cog.rank_topics('good evening everyone') == []


def test_ranking_is_case_insensitive(cog: FAQ) -> None:
    assert cog.rank_topics('How do I APPLY for ATC?') == ['ATC Application']


def test_triggers_match_whole_words_only(cog: FAQ) -> None:
    # 'waiter' and 'timetable' contain trigger words but are not them.
    assert cog.rank_topics('the waiter checked the timetable') == []


def test_tied_topics_fall_back_to_definition_order(cog: FAQ) -> None:
    # Both score 1.5: one unique word each, plus the shared 'training'.
    assert cog.rank_topics('atc training, what is the time?') == [
        'ATC Application',
        'Waiting Time',
    ]


def test_only_qualifying_topics_are_ranked(cog: FAQ) -> None:
    # 'training' alone leaves ATC below its threshold of 2.
    assert cog.rank_topics('how long is the wait time for training?') == [
        'Waiting Time',
    ]
