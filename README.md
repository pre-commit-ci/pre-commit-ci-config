[![Build Status](https://dev.azure.com/asottile/asottile/_apis/build/status/pre-commit-ci.pre-commit-ci-config?branchName=main)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=68&branchName=main)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/asottile/asottile/68/main.svg)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=68&branchName=main)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/pre-commit-ci/pre-commit-ci-config/main.svg)](https://results.pre-commit.ci/latest/github/pre-commit-ci/pre-commit-ci-config/main)

pre-commit-ci-config
====================

validation for [pre-commit.ci](https://pre-commit.ci) configuration

## installation

`pip install pre-commit-ci-config`

## api

### `pre_commit_ci_config.SCHEMA`

a [cfgv](https://github.com/asottile/cfgv) schema.

the expected input to this schema is the loaded top-level pre-commit
configuration.

```pycon
>>> import cfgv
>>> from pre_commit.clientlib import load_config
>>> from pre_commit_ci_config import SCHEMA
>>> cfg = load_config('.pre-commit-config.yaml')
>>> cfg = cfgv.validate(cfg, SCHEMA)
>>> cfg = cfgv.apply_defaults(cfg, SCHEMA)
```

### `check-pre-commit-ci-config`

a commandline tool to validate the configuration

```console
$ check-pre-commit-ci-config .pre-commit-config.yaml
$
```

## as a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/pre-commit-ci/pre-commit-ci-config
    rev: v1.5.1
    hooks:
    -   id: check-pre-commit-ci-config
```
