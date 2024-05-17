import logging
from colorlog import ColoredFormatter

def set_logger(config: dict):
    
    logger = logging.getLogger("teletop")
    
    log_level_str = "info"
    log_level = logging.INFO
    
    config_log_level_str : str | None = config.get('LOG_LEVEL', None)
    config_env = config.get('ENV', None)
    
    if config_log_level_str is not None: 
        log_level_str = config_log_level_str.lower()
    elif config_env is not None:
        if config_env == "development":
            log_level_str = "debug"

    if log_level_str == "info":
        pass
    elif log_level_str == "debug":
        log_level = logging.DEBUG
    elif log_level_str == "warning":
        log_level = logging.WARNING
    elif log_level_str == "error":
        log_level = logging.ERROR
    elif log_level_str == "critical":
        log_level = logging.CRITICAL
    else:
        raise Exception(f"unknown log level: {log_level_str}")
    
    logger.setLevel(log_level)
        
    formatter = ColoredFormatter(
        "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )

    # 创建一个流处理器
    stream = logging.StreamHandler()
    stream.setLevel(log_level)
    stream.setFormatter(formatter)
    logger.addHandler(stream)