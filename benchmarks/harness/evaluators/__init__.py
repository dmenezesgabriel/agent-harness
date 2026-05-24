from harness.evaluators.behave_evaluator import BehaveEvaluator
from harness.evaluators.code_evaluator import CodeEvaluator
from harness.evaluators.plan_evaluator import PlanEvaluator
from harness.registry import evaluator_registry

evaluator_registry.register("plan", PlanEvaluator)
evaluator_registry.register("code", CodeEvaluator)
evaluator_registry.register("behave", BehaveEvaluator)
