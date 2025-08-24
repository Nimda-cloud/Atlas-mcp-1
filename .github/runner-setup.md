# Self-hosted macOS Runner Setup

To complete the automation loop (agent PR → CI (Linux+macOS) → auto-merge → local macOS verification), set up a self-hosted runner on your Mac.

Steps:

1) Create macOS self-hosted runner in GitHub
   - Go to: GitHub repo → Settings → Actions → Runners → New self-hosted runner
   - Choose: macOS x64
   - Follow the on-screen script to download & configure the runner
   - Recommended labels: `macOS`, `X64`

2) Install prerequisites on the runner machine
   - Xcode CLT: `xcode-select --install`
   - Homebrew (optional) and Docker Desktop (optional for docker compose checks)
   - kubectl (optional) for kustomize dry-run

3) Ensure Python 3.11 is available
   - The workflow uses actions/setup-python to install 3.11, so no system change is required, but internet access is needed

4) Start the runner
   - Keep the runner process alive (launch at login recommended)

Once configured, every push to `main` will trigger `Post-merge local verification`, running tests and quick Docker/K8s validations on your Mac.
