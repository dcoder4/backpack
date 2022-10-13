''' Serializers/Deserializers (SerDe) convert between configuration strings (or numbers) and
different Python structures.

You should subclass :class:`ConfigSerDeBase` and override the following static fields:

- ``name``: the description of the structure this serde can convert, for example "Comma-separated
  list of integers". This text will be used in the documentation generated by the ConfigBase CLI.
- ``serialize``: Take the Python structure and returns a string representation.
- ``deserialize``: Take a string representation of the value and return a Python structure.
'''

from typing import Any, List, Sequence, Mapping
from abc import ABC, abstractmethod

class ConfigSerDeBase(ABC):
    ''' Defines a serializer / deserializer interface. '''

    description : str = 'The base serde encodes and decodes strings to themselves.'
    ''' A textual description how the object is encoded in the string. Will be used in docs. '''

    example : str = 'abcdefgh'
    ''' Provide a textual example of the encoded string. Will be used in docs. '''

    @staticmethod
    @abstractmethod
    def serialize(value: Any, metadata: Mapping[str, Any]={}) -> str:
        ''' Serializes a config value to a string.

        Args:
            value (Any): a Python object to be serialized.
            metadata (Mapping[str, Any]): Additional metadata to be passed to SerDe implementations.

        Returns:
            The object serialized into a string.
        '''
        return str(value)

    @staticmethod
    @abstractmethod
    def deserialize(value: str, metadata: Mapping[str, Any]={}) -> Any:
        ''' Deserializes a string to a config value.

        Args:
            value (str): a Python object serialized into a string
            metadata (Mapping[str, Any]): Additional metadata to be passed to SerDe implementations.

        Returns:
            The the restored Python object.
        '''
        return value


class IntegerListSerDe(ConfigSerDeBase):
    ''' De/serializes a string containing a comma-separated list of integers.'''

    description : str = 'Comma-separated list of integers'
    example: str = '0, 1, 2'

    @staticmethod
    def serialize(value: Sequence[int], metadata: Mapping[str, Any]={}) -> str:
        ''' Serializes a list of integers into a string.

        Args:
            value (Sequence[int]): The list of integers.

        Returns:
            The list of integers serialized into a string.
        '''
        sep = metadata.get('separator', ', ')
        return sep.join(str(e) for e in value)

    @staticmethod
    def deserialize(value: str, metadata: Mapping[str, Any]={}) -> List[int]:
        '''Restores a list of integers from a string.

        Args:
            value (str): A string containing a serialized list of integers.

        Returns:
            The list of integers restored from the string.

        Raises:
            Exception: exceptions related to invalid string format.
        '''
        sep = metadata.get('separator', ',')
        return [int(e) for e in value.split(sep)]
