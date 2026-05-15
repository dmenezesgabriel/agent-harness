# Specialist Audit Routing

Use specialist audits only when the request or risk justifies extra depth.

## Use `test-quality-audit` when
- the request asks whether tests are meaningful or sufficient
- new tests were added but their regression value is unclear
- failures suggest weak coverage, brittle assertions, or missing protection around the changed behavior
- validation passes technically, but confidence in the tests is still low

## Use `security-vulnerability-audit` when
- the change touches auth, authorization, secrets, sensitive data, trust boundaries, external input, file handling, outbound requests, admin capabilities, payments, or dependency risk
- the request explicitly asks for security review
- the change opens or modifies a path where misuse could matter even if normal tests pass

## Do not escalate when
- the change is ordinary and low-risk
- targeted validation already covers the relevant behavior
- there is no specific test-quality or security concern
- escalation would duplicate routine checks without adding decision-useful signal
