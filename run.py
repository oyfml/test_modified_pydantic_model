from pydantic import BaseModel as PydanticBaseModel
import inspect
from typing import Any, Optional, List
from copy import deepcopy
import ast
import textwrap
import pytest


class BaseModel(PydanticBaseModel):
    class Config:
        validate_assignment = True
        validate_all = True
        extra = "ignore"
        use_enum_values = True
    
    def __hash__(self):
        """
        Allows subclasses of base model to be hashable
        Convert representation of model attrs as key to get hash value
        Note: all Models must have at least 1 unique attr
        """
        return hash(repr((type(self),) + tuple(self.__dict__.values())))

def Skip(_type: Any):
    # does nothing but annotates
    return _type

class AdvancedBaseModel(BaseModel):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__( *args, **kwargs)
        # annotations = deepcopy(self.__annotations__)
        # fields = deepcopy(self.__fields__)
        # fields_set = deepcopy(self.__fields_set__)

        # parse class definition's abstract syntax tree after removing indentation
        cls_def: ast.ClassDef = ast.parse(textwrap.dedent(inspect.getsource(self.__class__))).body[0]
        # get all assignments with type annotation under class; i.e. x: int or y: str = 1
        ann_assign_list: List[ast.AnnAssign] = filter(lambda x: isinstance(x, ast.AnnAssign), cls_def.body)
        for ann_assign in ann_assign_list:
            # look for annotations wrapped with Skip function
            if isinstance(ann_assign.annotation, ast.Call):
                func_name_obj: ast.Name = ann_assign.annotation.func
                field_name_obj: ast.Name = ann_assign.target
                if func_name_obj.id == "Skip":
                    field_name = field_name_obj.id
                    # remove key field if optional and unset
                    if (
                        not self.__fields__[field_name].required
                        and self.__dict__[field_name] is None
                    ):
                        self.__delattr__(field_name)


        # for field_repr in inspect.getsource(self.__class__).split("\n")[1:]:
        #     if "# skip" in field_repr.lower():
        #         field_name = field_repr.split(":")[0].strip()
        #         if not fields[field_name].required and self.__dict__[field_name] is None:
        #             self.__delattr__(field_name)
        #             annotations.pop(field_name)
        #             fields.pop(field_name)
        #             if field_name in fields_set:
        #                 fields_set.remove(field_name)

        # object.__setattr__(self, "__annotations__", annotations)
        # object.__setattr__(self, "__fields__", fields)
        # object.__setattr__(self, "__fields_set__", fields_set)
    
    # def dict(self, *args: Any, **kwargs: Any):
    #     return self.dict(*args, **kwargs, exclude_unset=True)

def test_outer_skip():
    # Outer model is modified 
    class Inner(BaseModel):
        e: int
        f: Optional[int]
        g: Skip(Optional[List[str]]) # does nothing

    class Outer(AdvancedBaseModel):
        a: str
        b: Optional[str]
        c: Skip(Optional[List[str]]) # skip
        d: Inner

    t = Outer(a=1, d=Inner(e=1,f=2))
    t1 = Outer(a=1, c=None, d=Inner(e=1,f=2))
    t2 = Outer(a=1, c=[2], d=Inner(e=1,f=2))

    # skip c if assigned as None
    assert t.dict() == {'a': '1', 'b': None, 'd': {'e': 1, 'f': 2, 'g': None}}
    assert t1.dict() == {'a': '1', 'b': None, 'd': {'e': 1, 'f': 2, 'g': None}}
    assert t2.dict() == {'a': '1', 'b': None, 'c': ['2'], 'd': {'e': 1, 'f': 2, 'g': None}}


def test_inner_skip():
    class Inner(AdvancedBaseModel):
        e: int
        f: Optional[int]
        g: Skip(Optional[List[str]]) # skip

    class Outer(BaseModel):
        a: str
        b: Optional[str]
        c: Skip(Optional[List[str]]) # does nothing
        d: Inner

    t = Outer(a=1, d=Inner(e=1,f=2))
    t1 = Outer(a=1, c=None, d=Inner(e=1,f=2))
    t2 = Outer(a=1, c=[2], d=Inner(e=1,f=2))
    
    assert t.dict() == {'a': '1', 'b': None, 'c': None, 'd': {'e': 1, 'f': 2}}
    assert t1.dict() == {'a': '1', 'b': None, 'c': None, 'd': {'e': 1, 'f': 2}}
    assert t2.dict() == {'a': '1', 'b': None, 'c': ['2'], 'd': {'e': 1, 'f': 2}}
  
def test_both_skip():
    # Both models are modified 
    class Inner(AdvancedBaseModel):
        e: int
        f: Optional[int]
        g: Skip(Optional[List[str]]) # skip

    class Outer(AdvancedBaseModel):
        a: str
        b: Optional[str]
        c: Skip(Optional[List[str]]) # skip
        d: Inner

    t = Outer(a=1, d=Inner(e=1,f=2))
    t1 = Outer(a=1, c=None, d=Inner(e=1,f=2))
    t2 = Outer(a=1, c=[2], d=Inner(e=1,f=2))

    # skip c and g if assigned as None
    assert t.dict() == {'a': '1', 'b': None, 'd': {'e': 1, 'f': 2}}
    assert t1.dict() == {'a': '1', 'b': None, 'd': {'e': 1, 'f': 2}}
    assert t2.dict() == {'a': '1', 'b': None, 'c': ['2'], 'd': {'e': 1, 'f': 2}}


def test_nested_skip():
    class Inner(BaseModel):
        e: int
        f: Optional[int]
        g: Skip(Optional[List[str]]) # skip

    class Outer(AdvancedBaseModel):
        a: str
        b: Optional[str]
        c: Skip(Optional[Inner]) # skip

    t = Outer(a=1)
    t1 = Outer(a=1, c=None)
    t2 = Outer(a=1, c=Inner(e=1,f=2))
    
    assert t.dict() == {'a': '1', 'b': None}
    assert t1.dict() == {'a': '1', 'b': None}
    assert t2.dict() == {'a': '1', 'b': None, 'c': {'e': 1, 'f': 2, 'g': None}}
