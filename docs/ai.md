# AI Integration

The optional AI parser uses Pydantic AI structured output to populate
`GatewayScaffoldConfig`.

It does not generate source code. If AI dependencies or model configuration are
missing, the CLI still works with prompts and explicit flags.
