"""kipimo — Swahili agent-task evaluation for the East Africa coordination stack."""

from .cli import __version__ as __version__
from .cli import load_tasks as load_tasks
from .cli import score_file as score_file
from .cli import score_one as score_one
from .harness import run_scorecard as run_scorecard
from .harness import run_target as run_target
from .pareto import analyze as analyze
from .pareto import cheapest_qualifier as cheapest_qualifier
from .pareto import pareto_frontier as pareto_frontier
from .targets import FAMILIES as FAMILIES
from .targets import TARGETS as TARGETS
from .targets import get_target as get_target
from .targets import list_targets as list_targets
