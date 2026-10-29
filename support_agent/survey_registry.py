"""Explicit instrument/language/key identities; candidates never contain runnable items."""
from dataclasses import dataclass
from .psychometrics import Questionnaire
from .wellbeing_tests import TIPI
from .published_personality_tests import MINI_IPIP, RSES
from .research_wellbeing_tests import SWLS, COPING_CONFIDENCE
from .attachment_questions import ATTACHMENT_EXPLORATION
from .long_personality_tests import IPIP50, SWLS3


@dataclass(frozen=True)
class SurveyVersion:
    id: str
    construct_id: str
    instrument_id: str
    version: str
    language_version: str
    scoring_key_version: str
    definition: Questionnaire | None
    enabled: bool
    notes: str
    item_count: int
    source_url: str
    license_notice: str
    validation_population: str


def _registered(q, construct, instrument, version):
    return SurveyVersion(
        f'{instrument}:{version}:zh-project-v1:key-v1', construct, instrument, version,
        'zh-project-v1', 'key-v1', q, True, q.translation_note, len(q.items),
        q.source_url, q.license_notice,
        '本项目中文译文/原创题目未经中文样本信效度验证；不把原文研究人群的结果外推为本项目验证。',
    )


def _candidate(construct, instrument, version, count, url):
    return SurveyVersion(
        f'{instrument}:{version}:zh-pending:key-pending', construct, instrument, version,
        'zh-pending', 'key-pending', None, False,
        '候选，未接入题项；须逐项核实具体中文版、题序、计分、量程与适用许可后另行启用。',
        count, url, '本项目尚未完成该具体版本及中文材料的许可核实。', '未核实，不宣称项目验证。',
    )


SURVEY_VERSIONS = (
    _registered(TIPI,'big_five','tipi','10'),
    _registered(MINI_IPIP,'big_five','mini_ipip','20'),
    _registered(IPIP50,'big_five','ipip50','factor-markers-50'),
    _registered(RSES,'self_esteem','rses','10'),
    _registered(SWLS,'life_satisfaction','swls','5'),
    _registered(SWLS3,'life_satisfaction','swls','3'),
    _registered(ATTACHMENT_EXPLORATION,'attachment','attachment_original','12'),
    _registered(COPING_CONFIDENCE,'coping','coping_original','6'),
    _candidate('big_five','ipip100','factor-markers-100',100,'https://ipip.ori.org/newBigFive5broadKey.htm'),
    *(_candidate('big_five','bfi2',str(n),n,'https://www.ocf.berkeley.edu/~johnlab/measures') for n in (60,30,15)),
    _candidate('attachment','ecr_r','36',36,'https://labs.psychology.illinois.edu/~rcfraley/measures/ecrr.htm'),
    _candidate('attachment','ecr_rs','9',9,'https://labs.psychology.illinois.edu/~rcfraley/measures/relstructures.htm'),
    _candidate('attachment','ecr_s','12',12,'https://pubmed.ncbi.nlm.nih.gov/17437384/'),
)
_BY_ID = {v.id:v for v in SURVEY_VERSIONS}


def get_version(version_id: str) -> SurveyVersion:
    """Require a complete version ID; unknown IDs raise KeyError."""
    return _BY_ID[version_id]


def list_versions(construct_id: str | None = None) -> tuple[SurveyVersion, ...]:
    """Include disabled candidates, so callers can explain pending versions."""
    return tuple(v for v in SURVEY_VERSIONS if construct_id is None or v.construct_id==construct_id)
