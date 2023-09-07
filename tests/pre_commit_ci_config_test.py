from __future__ import annotations

import cfgv
import pytest

from pre_commit_ci_config import main
from pre_commit_ci_config import SCHEMA


def _error_to_trace(e):
    ret = []
    while isinstance(e.error_msg, cfgv.ValidationError):
        ret.append(e.ctx)
        e = e.error_msg
    ret.append(e.error_msg)
    return tuple(ret)


def test_apply_defaults():
    ret = cfgv.apply_defaults({'repos': []}, SCHEMA)
    assert ret == {
        'ci': {
            'autofix_commit_msg': (
                '[pre-commit.ci] auto fixes from pre-commit.com hooks\n\n'
                'for more information, see https://pre-commit.ci\n'
            ),
            'autofix_prs': True,
            'autoupdate_branch': '',
            'autoupdate_commit_msg': '[pre-commit.ci] pre-commit autoupdate',
            'autoupdate_schedule': 'weekly',
            'skip': [],
            'submodules': False,
        },
        'repos': [],
    }


def test_autoupdate_branch_ok():
    cfg = {'ci': {'autoupdate_branch': 'dev'}, 'repos': []}
    cfgv.validate(cfg, SCHEMA)


def test_autoupdate_branch_does_not_allow_our_branch_name():
    cfg = {
        'ci': {'autoupdate_branch': 'pre-commit-ci-update-config'},
        'repos': [],
    }
    with pytest.raises(cfgv.ValidationError) as excinfo:
        cfgv.validate(cfg, SCHEMA)
    assert _error_to_trace(excinfo.value) == (
        'At Config()',
        'At key: ci',
        'At CI()',
        'At key: autoupdate_branch',
        "autoupdate branch cannot be 'pre-commit-ci-update-config'",
    )


def test_autoupdate_commit_msg_cannot_be_empty():
    cfg = {'ci': {'autoupdate_commit_msg': ''}, 'repos': []}
    with pytest.raises(cfgv.ValidationError) as excinfo:
        cfgv.validate(cfg, SCHEMA)
    assert _error_to_trace(excinfo.value) == (
        'At Config()',
        'At key: ci',
        'At CI()',
        'At key: autoupdate_commit_msg',
        'string cannot be empty',
    )


def test_autoupdate_commit_msg_ok_if_provided():
    cfg = {'ci': {'autoupdate_commit_msg': 'autoupdate'}, 'repos': []}
    cfgv.validate(cfg, SCHEMA)


def test_skip_references_hook():
    cfg = {
        'ci': {'skip': ['identity']},
        'repos': [{'repo': 'meta', 'hooks': [{'id': 'identity'}]}],
    }
    cfgv.validate(cfg, SCHEMA)


def test_skip_referencing_missing_hook():
    cfg = {'ci': {'skip': ['identity']}, 'repos': []}
    with pytest.raises(cfgv.ValidationError) as excinfo:
        cfgv.validate(cfg, SCHEMA)
    assert _error_to_trace(excinfo.value) == (
        'At Config()',
        'At key: ci',
        'At key: skip',
        'unexpected hook ids: identity',
    )


def test_skip_references_hook_with_alias():
    cfg = {
        'ci': {'skip': ['alternate-identity']},
        'repos': [
            {
                'repo': 'meta',
                'hooks': [
                    {
                        'id': 'identity',
                        'alias': 'alternate-identity',
                    },
                ],
            },
        ],
    }
    cfgv.validate(cfg, SCHEMA)


def test_main_ok(tmpdir):
    cfg_s = '''\
ci:
    skip: [identity]
repos:
-   repo: meta
    hooks:
    -   id: identity
'''
    cfg = tmpdir.join('cfg.yaml')
    cfg.write(cfg_s)

    assert not main((str(cfg),))


def test_main_failing(tmpdir, capsys):
    cfg_s = '''\
ci:
    skip: [identity]
repos: []
'''
    cfg = tmpdir.join('cfg.yaml')
    cfg.write(cfg_s)

    assert main((str(cfg),))

    out, _ = capsys.readouterr()

    # TODO: cfgv produces trailing whitespace sometimes
    assert ' \n' in out
    out = out.replace(' \n', '\n')

    assert out == f'''\
=====>
==> File {cfg}
==> At Config()
==> At key: ci
==> At key: skip
=====> unexpected hook ids: identity
'''
