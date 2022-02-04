# Modified Pydantic Model that allows Optional field keys

- Pydantic v1.x.x does not support Optional keys, all model definition enforces keys to be present.
- This repo introduces a subclass to allow proper definition of Optional field keys
- Ref: [issue](https://github.com/samuelcolvin/pydantic/issues/1223)


## Usage
Inherit modified class and annotation with Skip function wrapping field type
```
class ExampleModel(AdvancedBaseModel):
    a: Skip(Optional[List[str]) # optional key
    b: Skip(Optional[str], default="sample_string") # optional key with default value
    c: Optional[type] # optional value but mandatory key
    d: Skip(str) # does nothing
```

## Installation
`pip install -r requirements.txt`

## Run Test Cases
`pytest run.py`

## Context
When defining pydantic model, the keys (attributes) in the model are mandatory.
e.g.
```
class Model(BaseModel):
   a: str
   b: Optional[str]
```
__a__ and __b__ must be keys in the dictionary.

If partial models / optional keys are required, the following can be done:

Assume b to be intended as optional key (note diff with optional value)

`{ "a": "1", "b": null } `

OR

`{ "a": "1" }`

then model definition should be (in order to achieve it):

e.g.
```
class M1(BaseModel):
   a: str
   b: Optional[str]

class M2(BaseModel):
   a: str

Model = Union[M1, M2]
```
OR
```
class M2(BaseModel):
   a: str

class M1(M2):
   b: Optional[str]

Model = Union[M1, M2]
```
#### Problem:
Defining partial models or model versioning can be problematic as seen in the above example.
This form of expression is not scalable when model has many keys.


Fortunately, Pydantic will support this notation in __v2__:
```
Optional[type] <- optional key
Optional[type] = None <-optional value but mandatory key
```
but in the mean time: v2's
```
Optional[type] <- optional key
Optional[type] = None <-optional value but mandatory key
```
is equivalent to:
```
Skip(Optional[type]) <- optional key
Optional[type] <-optional value but mandatory key
Union[type, None] <-optional value but mandatory key
type = None <-optional value but mandatory key
```
