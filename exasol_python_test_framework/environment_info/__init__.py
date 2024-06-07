import json


class EnvironmentInfo:
    """
    Recursive class which converts a given dictionary to attributes of the instance.
    """
    def __init__(self, d):
        for k, v in d.items():
            if isinstance(k, (list, tuple)):
                setattr(self, k, [EnvironmentInfo(x) if isinstance(x, dict) else x for x in v])
            else:
                setattr(self, k, EnvironmentInfo(v) if isinstance(v, dict) else v)


def from_environment_info_file() -> EnvironmentInfo:
    with open("/environment_info.json", "r") as f:
        env_info_dict = json.load(f)
        return EnvironmentInfo(env_info_dict)
