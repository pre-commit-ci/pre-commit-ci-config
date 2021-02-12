from __future__ import annotations

import argparse
import functools
from typing import Any
from typing import Sequence

import cfgv
import yaml

Loader = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
yaml_load = functools.partial(yaml.load, Loader=Loader)


class ValidateSkip:
    def check(self, dct: dict[str, Any]) -> None:
        all_ids = {
            hook['id']
            for repo in dct['repos']
            for hook in repo['hooks']
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
)

CONFIG_REPO_DICT = cfgv.Map(
    'Repository', 'repo',

    cfgv.Required('repo', cfgv.check_string),
    cfgv.RequiredRecurse('hooks', cfgv.Array(HOOK_DICT)),
)

CI_DICT = cfgv.Map(
    'CI', None,

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
    exit(main())
