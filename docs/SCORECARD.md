# The Swahili Open-Model Scorecard — protocol

kipimo v0.2 adds a target registry (`kipimo targets`) so published scorecards
name models consistently across three families: `closed-api`, `open-weight`,
and `small-open`. The third family exists because small distilled models are
the realistic deployment tier for most of East Africa, and nobody measures
their Swahili task competence. On this scorecard they are first-class citizens.

## Rules for a publishable run

1. **Reproducible:** publish the exact model id, endpoint type (vendor API /
   hosted open weights / self-hosted), temperature (0), and kipimo version.
2. **Untuned:** no prompt engineering beyond `examples/generate_predictions.py`'s
   fixed instruction. The scorecard measures models, not prompting skill.
3. **Complete:** all 46 tasks; missing predictions score 0 and are reported.
4. **Labeled:** every run is DEMO until independently re-run by a second party;
   REAL after one independent reproduction within ±2 points overall.
5. **Caveated:** v0.x is a seed benchmark in simple-register Swahili pending
   native-speaker review (issue #1). Scores indicate stack-routing competence,
   not general Swahili fluency, and must not be a sole deployment gate.

## Publishing

Results go to the leaderboard Space (huggingface.co/spaces/gmahia/kipimo-leaderboard)
with the predictions file attached. Disagreements are settled by re-running, not
by argument — the scorer is deterministic and never calls a model.
