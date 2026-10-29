"""Pure local scoring of explicitly defined questionnaire dimensions.

Results preserve raw answers and expose dimension sums and means. Unrelated
dimensions are never combined into a global score or converted to percentages.
Use ``dataclasses.asdict(result)`` when an exportable dictionary is needed.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class TestItem:
    id: str
    text: str
    dimension: str
    reverse: bool = False


@dataclass(frozen=True)
class Questionnaire:
    id: str
    title: str
    description: str
    items: tuple[TestItem, ...]
    options: tuple[str, ...]
    min_score: int
    dimension_labels: dict[str, str]
    source_name: str
    source_url: str
    license_notice: str
    translation_note: str
    display: str = 'mean'
    interpretation: str = ''

    @property
    def max_score(self) -> int:
        return self.min_score + len(self.options) - 1


@dataclass(frozen=True)
class DimensionResult:
    key: str
    label: str
    total: int
    mean: float
    count: int
    min_total: int
    max_total: int
    min_value: int
    max_value: int


@dataclass(frozen=True)
class QuestionnaireResult:
    test_id: str
    dimensions: dict[str, DimensionResult]
    answers: dict[str, int]
    version_id: str | None = None


def _validate_definition(definition: Questionnaire) -> None:
    if type(definition.min_score) is not int:
        raise ValueError('The minimum score must be an integer.')
    if len(definition.options) < 2:
        raise ValueError('At least two response options are required.')
    if not definition.items:
        raise ValueError('At least one questionnaire item is required.')
    ids = [item.id for item in definition.items]
    if len(set(ids)) != len(ids):
        raise ValueError('Questionnaire item IDs must be unique.')
    if any(not isinstance(item_id, str) or not item_id for item_id in ids):
        raise ValueError('Questionnaire item IDs must be nonempty strings.')
    dimensions = {item.dimension for item in definition.items}
    if dimensions != set(definition.dimension_labels):
        raise ValueError('Dimension labels must match the item dimensions exactly.')


def score_questionnaire(
    definition: Questionnaire, answers: Mapping[str, int],
) -> QuestionnaireResult:
    """Score complete integer answers without imputation or interpretation.

    Every item ID must occur exactly once in the answer mapping, with no extra
    IDs. Reverse scoring reflects the raw value through the scale endpoints.
    Invalid definitions or answers raise ``ValueError`` before a result exists.
    """
    _validate_definition(definition)
    item_ids = {item.id for item in definition.items}
    if not isinstance(answers, Mapping) or set(answers) != item_ids:
        raise ValueError('Answers must contain exactly all questionnaire item IDs.')
    minimum, maximum = definition.min_score, definition.max_score
    if any(type(value) is not int or not minimum <= value <= maximum for value in answers.values()):
        raise ValueError('Every answer must be an integer within the response scale.')

    totals = {key: 0 for key in definition.dimension_labels}
    counts = {key: 0 for key in definition.dimension_labels}
    for item in definition.items:
        raw_value = answers[item.id]
        value = minimum + maximum - raw_value if item.reverse else raw_value
        totals[item.dimension] += value
        counts[item.dimension] += 1
    dimensions = {
        key: DimensionResult(
            key=key, label=label, total=totals[key],
            mean=totals[key] / counts[key], count=counts[key],
            min_total=minimum * counts[key], max_total=maximum * counts[key],
            min_value=minimum, max_value=maximum,
        )
        for key, label in definition.dimension_labels.items()
    }
    return QuestionnaireResult(
        test_id=definition.id, dimensions=dimensions,
        answers={item.id: answers[item.id] for item in definition.items},
    )
