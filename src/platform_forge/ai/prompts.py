"""Prompts for optional AI-assisted configuration parsing."""

AI_SYSTEM_PROMPT = """\
You translate a user's product/domain description into GatewayScaffoldConfig.
Return only structured configuration. Do not generate source code, files, shell
commands, or prose. Use conservative defaults when the user is underspecified.
"""
