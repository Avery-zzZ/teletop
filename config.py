from dynaconf import Dynaconf

settings: dict = Dynaconf(
    envvar_prefix="TELETOP",
    settings_files=["settings.toml", "settings_dev.toml"],
    load_dotenv=True,
    dotenv_override=True
).as_dict()