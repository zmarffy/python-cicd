import os
from json import dumps

from pkg_resources import packaging

version = packaging.version.parse(os.environ["VERSION"])

print(
    dumps(
        {
            "local": version.local is not None,
            "prerelease": version.is_prerelease
        }
    )
)
