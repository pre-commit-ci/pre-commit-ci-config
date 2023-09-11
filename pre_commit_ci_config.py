from __future__ import annotations

import argparse
import functools
from typing import Any
from typing import Sequence

import cfgv
import yaml

Loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
yaml_load = functools.partial(yaml.load, Loader=Loader)


def _check_non_empty_string(val: str) -> None:
    if not val:
        raise cfgv.ValidationError('string cannot be empty')


def _check_autoupdate_branch(val: str) -> None:
    if val == 'pre-commit-ci-update-config':
        raise cfgv.ValidationError(f'autoupdate branch cannot be {val!r}')


class ValidateSkip:
    def check(self, dct: dict[str, Any]) -> None:
        all_ids = {
            hook_id
            for repo in dct['repos']
            for hook in repo['hooks']
            for hook_id in (hook['id'], hook.get('alias'))
            if hook_id is not None
        }
        unexpected_skip = set(dct.get('ci', {}).get('skip', ())) - all_ids
        if unexpected_skip:
            with cfgv.validate_context('At key: ci'):
                with cfgv.validate_context('At key: skip'):
                    raise cfgv.ValidationError(
                        f'unexpected hook ids: '
                        f'{", ".join(sorted(unexpected_skip))}',
                    )

    apply_default = cfgv.Required.apply_default
    remove_default = cfgv.Required.remove_default


HOOK_DICT = cfgv.Map(
    'Hook', 'id',

    cfgv.Required('id', cfgv.check_string),
    cfgv.OptionalNoDefault('alias', cfgv.check_string),
)

CONFIG_REPO_DICT = cfgv.Map(
    'Repository', 'repo',

    cfgv.Required('repo', cfgv.check_string),
    cfgv.RequiredRecurse('hooks', cfgv.Array(HOOK_DICT)),
)

AUTOFIX_DEFAULT_COMMIT_MSG = '''\
[pre-commit.ci] auto fixes from pre-commit.com hooks

for more information, see https://pre-commit.ci
'''

CI_DICT = cfgv.Map(
    'CI', None,

    cfgv.Optional(
        'autofix_commit_msg',
        cfgv.check_and(cfgv.check_string, _check_non_empty_string),
        AUTOFIX_DEFAULT_COMMIT_MSG,
    ),
    cfgv.Optional('autofix_prs', cfgv.check_bool, True),
    cfgv.Optional(
        'autoupdate_branch',
        cfgv.check_and(cfgv.check_string, _check_autoupdate_branch),
        '',
    ),
    cfgv.Optional(
        'autoupdate_commit_msg',
        cfgv.check_and(cfgv.check_string, _check_non_empty_string),
        '[pre-commit.ci] pre-commit autoupdate',
    ),
    cfgv.Optional(
        'autoupdate_schedule',
        cfgv.check_one_of(('weekly', 'monthly', 'quarterly')),
        'weekly',
    ),
    cfgv.Optional('skip', cfgv.check_array(cfgv.check_string), []),
    cfgv.Optional('submodules', cfgv.check_bool, False),
)

SCHEMA = cfgv.Map(
    'Config', None,

    # to cross-validate hook values
    cfgv.RequiredRecurse('repos', cfgv.Array(CONFIG_REPO_DICT)),

    # our configuration
    cfgv.OptionalRecurse('ci', CI_DICT, {}),
    ValidateSkip(),
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        try:
            cfgv.load_from_filename(
                filename,
                schema=SCHEMA,
                load_strategy=yaml_load,
            )
        except cfgv.ValidationError as e:
            print(str(e).strip())
            retv = 1
    return retv


if __name__ == '__main__':
    raise SystemExit(main())
