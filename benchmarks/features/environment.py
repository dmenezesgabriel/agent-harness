"""Behave environment hooks.

The workspace snapshot is written to a temp directory by BehaveEvaluator
before invoking behave. The path is passed via behave's userdata:
  --define workspace=/tmp/bench-behave-xyz
"""
from pathlib import Path


def before_all(context):
    ws = context.config.userdata.get("workspace", "")
    context.workspace = Path(ws) if ws else Path(".")


def before_scenario(context, scenario):
    # make workspace available as both Path and str for step convenience
    context.ws = context.workspace
