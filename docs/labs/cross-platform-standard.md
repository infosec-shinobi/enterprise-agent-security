# Cross-platform authoring standard for all labs

All future labs MUST support **Bash on Linux/macOS** and **PowerShell 5.1/7+ on Windows**.

## Documentation requirements

1. Every executable step has adjacent, labeled `bash` and `powershell` fenced code blocks, including setup, credentials, positive/negative tests, log inspection, troubleshooting and cleanup.
2. Even when commands are identical (e.g., `docker compose ps`), include both blocks for consistency.
3. Include prerequisites, expected HTTP status and response, common failure modes, and reset instructions.
4. Do not use Bash-only variable assignment (`TOKEN=$(...)`) in PowerShell blocks.
5. Use `curl.exe` in Windows PowerShell, not `curl` (which can alias to `Invoke-WebRequest`); do not rely on `-SkipHttpErrorCheck`, absent in Windows PowerShell 5.1.
6. Do not assume GNU utilities exist on macOS or Python is installed on Windows. Name required dependencies explicitly.
7. Keep secrets out of terminal history and public screenshots where practical. Use synthetic data and local-only ports.
8. Maintain equivalent outcomes across shells; test each command path on the stated OS/version before marking verified.
9. Distinguish expected authorization denial (403), authentication failure (401), and unavailable authorization dependency (503).
10. Use platform-independent automation (Docker Compose, pytest, etc.) where possible, but always document host commands for both platforms.

## Review checklist

- [ ] Bash commands reviewed/tested on Linux
- [ ] Bash commands reviewed/tested on macOS
- [ ] PowerShell commands reviewed/tested on Windows PowerShell 5.1
- [ ] PowerShell commands reviewed/tested on PowerShell 7
- [ ] Expected results and error conditions documented
- [ ] Cleanup documented for both shells
- [ ] Versions and untested combinations clearly disclosed

This is a **documentation requirement**, not a claim that every current lab has been tested on all four environments.
