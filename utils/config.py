import importlib

def name_to_class(cfg, **kwargs):
    if "name_config" in kwargs:
        name_config = kwargs["name_config"]
    else:
        name_config = cfg
    module = importlib.import_module(name_config.module_name)
    moduleclass = getattr(module, name_config.class_name)
    class_ = moduleclass(cfg, **kwargs)
    return class_