from enum import Enum

"""
 enum class
"""
class enumclass(Enum):
    @classmethod
    def is_member(cls, name):
        return name.upper() in cls._member_names_

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

