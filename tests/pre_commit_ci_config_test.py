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
            'autofix_prs': True,
            'skip': [],
            'submodules': False,
        },
        'repos': [],
    }


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
