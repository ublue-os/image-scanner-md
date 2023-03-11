# ublue-scanner
## Getting started
1. Get a github personal access token that gives `packages:read` access and
   put it in `.env` as `GITHUB_TOKEN`.

2. Install it
```bash
poetry install
```

2. Run it
```bash
poetry run ublue-scan --org <github org name>
```

In this example, we'd use `ublue-os` as the org name.

## Configuration
If you want to exclude certain images you can pass a `--config` option that is
a YAML file in the format of:

```yaml
ignores:
  - udev-rules
  - config
```