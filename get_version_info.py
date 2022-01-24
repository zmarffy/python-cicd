from glob import glob
from json import dumps

from pkg_resources import packaging

version_string = glob("dist/*.tar.gz")[0].split("-")[-1].removesuffix(".tar.gz")
version = packaging.version.parse(version_string)

print(
    dumps(
        {
            "version": version_string,
            "local": version.local is not None,
            "prerelease": version.is_prerelease
        }
    )
)
