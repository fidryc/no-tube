def mapping_to_obj(obj: dict, res_class_obj: type):
    return res_class_obj(**obj)