from __future__ import absolute_import, unicode_literals

import collections
import pickle
import re
import sys
from unittest import TestCase, main, SkipTest

from typing import Any
from typing import TypeVar, AnyStr
from typing import T, KT, VT  # Not in __all__.
from typing import Union, Optional
from typing import Tuple, List, MutableMapping
from typing import Callable
from typing import Generic, ClassVar
from typing import cast
from typing import Type
from typing import NewType
from typing import NamedTuple
from typing import IO, TextIO, BinaryIO
from typing import Pattern, Match
import abc
import typing
try:
    import collections.abc as collections_abc
except ImportError:
    import collections as collections_abc  # Fallback for PY3.2.


class BaseTestCase(TestCase):

    def assertIsSubclass(self, cls, class_or_tuple, msg=None):
        if not issubclass(cls, class_or_tuple):
            message = '%r is not a subclass of %r' % (cls, class_or_tuple)
            if msg is not None:
                message += ' : %s' % msg
            raise self.failureException(message)

    def assertNotIsSubclass(self, cls, class_or_tuple, msg=None):
        if issubclass(cls, class_or_tuple):
            message = '%r is a subclass of %r' % (cls, class_or_tuple)
            if msg is not None:
                message += ' : %s' % msg
            raise self.failureException(message)


class Employee(object):
    pass


class Manager(Employee):
    pass


class Founder(Employee):
    pass


class ManagingFounder(Manager, Founder):
    pass


class AnyTests(BaseTestCase):

    def test_any_instance_type_error(self):
        with self.assertRaises(TypeError):
            isinstance(42, Any)

    def test_any_subclass_type_error(self):
        with self.assertRaises(TypeError):
            issubclass(Employee, Any)
        with self.assertRaises(TypeError):
            issubclass(Any, Employee)

    def test_repr(self):
        self.assertEqual(repr(Any), 'typing.Any')

    def test_errors(self):
        with self.assertRaises(TypeError):
            issubclass(42, Any)
        with self.assertRaises(TypeError):
            Any[int]  # Any is not a generic type.

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
            class A(Any):
                pass
        with self.assertRaises(TypeError):
            class A(type(Any)):
                pass

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            Any()
        with self.assertRaises(TypeError):
            type(Any)()

    def test_cannot_subscript(self):
        with self.assertRaises(TypeError):
            Any[int]

    def test_any_is_subclass(self):
        # These expressions must simply not fail.
        typing.Match[Any]
        typing.Pattern[Any]
        typing.IO[Any]


class TypeVarTests(BaseTestCase):

    def test_basic_plain(self):
        T = TypeVar('T')
        # T equals itself.
        self.assertEqual(T, T)
        # T is an instance of TypeVar
        self.assertIsInstance(T, TypeVar)

    def test_typevar_instance_type_error(self):
        T = TypeVar('T')
        with self.assertRaises(TypeError):
            isinstance(42, T)

    def test_typevar_subclass_type_error(self):
        T = TypeVar('T')
        with self.assertRaises(TypeError):
            issubclass(int, T)
        with self.assertRaises(TypeError):
            issubclass(T, int)

    def test_constrained_error(self):
        with self.assertRaises(TypeError):
            X = TypeVar('X', int)
            X

    def test_union_unique(self):
        X = TypeVar('X')
        Y = TypeVar('Y')
        self.assertNotEqual(X, Y)
        self.assertEqual(Union[X], X)
        self.assertNotEqual(Union[X], Union[X, Y])
        self.assertEqual(Union[X, X], X)
        self.assertNotEqual(Union[X, int], Union[X])
        self.assertNotEqual(Union[X, int], Union[int])
        self.assertEqual(Union[X, int].__union_params__, (X, int))
        self.assertEqual(Union[X, int].__union_set_params__, {X, int})

    def test_union_constrained(self):
        A = TypeVar('A', str, bytes)
        self.assertNotEqual(Union[A, str], Union[A])

    def test_repr(self):
        self.assertEqual(repr(T), '~T')
        self.assertEqual(repr(KT), '~KT')
        self.assertEqual(repr(VT), '~VT')
        self.assertEqual(repr(AnyStr), '~AnyStr')
        T_co = TypeVar('T_co', covariant=True)
        self.assertEqual(repr(T_co), '+T_co')
        T_contra = TypeVar('T_contra', contravariant=True)
        self.assertEqual(repr(T_contra), '-T_contra')

    def test_no_redefinition(self):
        self.assertNotEqual(TypeVar('T'), TypeVar('T'))
        self.assertNotEqual(TypeVar('T', int, str), TypeVar('T', int, str))

    def test_cannot_subclass_vars(self):
        with self.assertRaises(TypeError):
            class V(TypeVar('T')):
                pass

    def test_cannot_subclass_var_itself(self):
        with self.assertRaises(TypeError):
            class V(TypeVar):
                pass

    def test_cannot_instantiate_vars(self):
        with self.assertRaises(TypeError):
            TypeVar('A')()

    def test_bound_errors(self):
        with self.assertRaises(TypeError):
            TypeVar('X', bound=42)
        with self.assertRaises(TypeError):
            TypeVar('X', str, float, bound=Employee)


class UnionTests(BaseTestCase):

    def test_basics(self):
        u = Union[int, float]
        self.assertNotEqual(u, Union)

    def test_subclass_error(self):
        with self.assertRaises(TypeError):
            issubclass(int, Union)
        with self.assertRaises(TypeError):
            issubclass(Union, int)
        with self.assertRaises(TypeError):
            issubclass(int, Union[int, str])
        with self.assertRaises(TypeError):
            issubclass(Union[int, str], int)

    def test_union_any(self):
        u = Union[Any]
        self.assertEqual(u, Any)
        u1 = Union[int, Any]
        u2 = Union[Any, int]
        u3 = Union[Any, object]
        self.assertEqual(u1, u2)
        self.assertNotEqual(u1, Any)
        self.assertNotEqual(u2, Any)
        self.assertNotEqual(u3, Any)

    def test_union_object(self):
        u = Union[object]
        self.assertEqual(u, object)
        u = Union[int, object]
        self.assertEqual(u, object)
        u = Union[object, int]
        self.assertEqual(u, object)

    def test_unordered(self):
        u1 = Union[int, float]
        u2 = Union[float, int]
        self.assertEqual(u1, u2)

    def test_single_class_disappears(self):
        t = Union[Employee]
        self.assertIs(t, Employee)

    def test_base_class_disappears(self):
        u = Union[Employee, Manager, int]
        self.assertEqual(u, Union[int, Employee])
        u = Union[Manager, int, Employee]
        self.assertEqual(u, Union[int, Employee])
        u = Union[Employee, Manager]
        self.assertIs(u, Employee)

    def test_union_union(self):
        u = Union[int, float]
        v = Union[u, Employee]
        self.assertEqual(v, Union[int, float, Employee])

    def test_repr(self):
        self.assertEqual(repr(Union), 'typing.Union')
        u = Union[Employee, int]
        self.assertEqual(repr(u), 'typing.Union[%s.Employee, int]' % __name__)
        u = Union[int, Employee]
        self.assertEqual(repr(u), 'typing.Union[int, %s.Employee]' % __name__)

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
            class C(Union):
                pass
        with self.assertRaises(TypeError):
            class C(type(Union)):
                pass
        with self.assertRaises(TypeError):
            class C(Union[int, str]):
                pass

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            Union()
        u = Union[int, float]
        with self.assertRaises(TypeError):
            u()
        with self.assertRaises(TypeError):
            type(u)()

    def test_union_generalization(self):
        self.assertFalse(Union[str, typing.Iterable[int]] == str)
        self.assertFalse(Union[str, typing.Iterable[int]] == typing.Iterable[int])
        self.assertTrue(Union[str, typing.Iterable] == typing.Iterable)

    def test_optional(self):
        o = Optional[int]
        u = Union[int, None]
        self.assertEqual(o, u)

    def test_empty(self):
        with self.assertRaises(TypeError):
            Union[()]

    def test_union_instance_type_error(self):
        with self.assertRaises(TypeError):
            isinstance(42, Union[int, str])

    def test_union_str_pattern(self):
        # Shouldn't crash; see http://bugs.python.org/issue25390
        A = Union[str, Pattern]
        A

    def test_etree(self):
        # See https://github.com/python/typing/issues/229
        # (Only relevant for Python 2.)
        try:
            from xml.etree.cElementTree import Element
        except ImportError:
            raise SkipTest("cElementTree not found")
        Union[Element, str]  # Shouldn't crash

        def Elem(*args):
            return Element(*args)

        Union[Elem, str]  # Nor should this


class TupleTests(BaseTestCase):

    def test_basics(self):
        with self.assertRaises(TypeError):
            issubclass(Tuple[int, str], Tuple)
        with self.assertRaises(TypeError):
            issubclass(Tuple, Tuple[int, str])
        with self.assertRaises(TypeError):
            issubclass(tuple, Tuple[int, str])

        class TP(tuple): pass
        self.assertTrue(issubclass(tuple, Tuple))
        self.assertTrue(issubclass(TP, Tuple))

    def test_equality(self):
        self.assertEqual(Tuple[int], Tuple[int])
        self.assertEqual(Tuple[int, ...], Tuple[int, ...])
        self.assertNotEqual(Tuple[int], Tuple[int, int])
        self.assertNotEqual(Tuple[int], Tuple[int, ...])

    def test_tuple_subclass(self):
        class MyTuple(tuple):
            pass
        self.assertTrue(issubclass(MyTuple, Tuple))

    def test_tuple_instance_type_error(self):
        with self.assertRaises(TypeError):
            isinstance((0, 0), Tuple[int, int])
        isinstance((0, 0), Tuple)

    def test_repr(self):
        self.assertEqual(repr(Tuple), 'typing.Tuple')
        self.assertEqual(repr(Tuple[()]), 'typing.Tuple[()]')
        self.assertEqual(repr(Tuple[int, float]), 'typing.Tuple[int, float]')
        self.assertEqual(repr(Tuple[int, ...]), 'typing.Tuple[int, ...]')

    def test_errors(self):
        with self.assertRaises(TypeError):
            issubclass(42, Tuple)
        with self.assertRaises(TypeError):
            issubclass(42, Tuple[int])


class CallableTests(BaseTestCase):

    def test_self_subclass(self):
        with self.assertRaises(TypeError):
            self.assertTrue(issubclass(type(lambda x: x), Callable[[int], int]))
        self.assertTrue(issubclass(type(lambda x: x), Callable))

    def test_eq_hash(self):
        self.assertEqual(Callable[[int], int], Callable[[int], int])
        self.assertEqual(len({Callable[[int], int], Callable[[int], int]}), 1)
        self.assertNotEqual(Callable[[int], int], Callable[[int], str])
        self.assertNotEqual(Callable[[int], int], Callable[[str], int])
        self.assertNotEqual(Callable[[int], int], Callable[[int, int], int])
        self.assertNotEqual(Callable[[int], int], Callable[[], int])
        self.assertNotEqual(Callable[[int], int], Callable)

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):

            class C(Callable):
                pass

        with self.assertRaises(TypeError):

            class C(type(Callable)):
                pass

        with self.assertRaises(TypeError):

            class C(Callable[[int], int]):
                pass

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            Callable()
        with self.assertRaises(TypeError):
            type(Callable)()
        c = Callable[[int], str]
        with self.assertRaises(TypeError):
            c()
        with self.assertRaises(TypeError):
            type(c)()

    def test_callable_instance_works(self):
        def f():
            pass
        self.assertIsInstance(f, Callable)
        self.assertNotIsInstance(None, Callable)

    def test_callable_instance_type_error(self):
        def f():
            pass
        with self.assertRaises(TypeError):
            self.assertIsInstance(f, Callable[[], None])
        with self.assertRaises(TypeError):
            self.assertIsInstance(f, Callable[[], Any])
        with self.assertRaises(TypeError):
            self.assertNotIsInstance(None, Callable[[], None])
        with self.assertRaises(TypeError):
            self.assertNotIsInstance(None, Callable[[], Any])

    def test_repr(self):
        ct0 = Callable[[], bool]
        self.assertEqual(repr(ct0), 'typing.Callable[[], bool]')
        ct2 = Callable[[str, float], int]
        self.assertEqual(repr(ct2), 'typing.Callable[[str, float], int]')
        ctv = Callable[..., str]
        self.assertEqual(repr(ctv), 'typing.Callable[..., str]')

    def test_ellipsis_in_generic(self):
        # Shouldn't crash; see https://github.com/python/typing/issues/259
        typing.List[Callable[..., str]]


XK = TypeVar('XK', unicode, bytes)
XV = TypeVar('XV')


class SimpleMapping(Generic[XK, XV]):

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, value):
        pass

    def get(self, key, default=None):
        pass


class MySimpleMapping(SimpleMapping[XK, XV]):

    def __init__(self):
        self.store = {}

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def get(self, key, default=None):
        try:
            return self.store[key]
        except KeyError:
            return default


class ProtocolTests(BaseTestCase):

    def test_supports_int(self):
        self.assertIsSubclass(int, typing.SupportsInt)
        self.assertNotIsSubclass(str, typing.SupportsInt)

    def test_supports_float(self):
        self.assertIsSubclass(float, typing.SupportsFloat)
        self.assertNotIsSubclass(str, typing.SupportsFloat)

    def test_supports_complex(self):

        # Note: complex itself doesn't have __complex__.
        class C(object):
            def __complex__(self):
                return 0j

        self.assertIsSubclass(C, typing.SupportsComplex)
        self.assertNotIsSubclass(str, typing.SupportsComplex)

    def test_supports_abs(self):
        self.assertIsSubclass(float, typing.SupportsAbs)
        self.assertIsSubclass(int, typing.SupportsAbs)
        self.assertNotIsSubclass(str, typing.SupportsAbs)

    def test_reversible(self):
        self.assertIsSubclass(list, typing.Reversible)
        self.assertNotIsSubclass(int, typing.Reversible)

    def test_protocol_instance_type_error(self):
        with self.assertRaises(TypeError):
            isinstance(0, typing.SupportsAbs)


class GenericTests(BaseTestCase):

    def test_basics(self):
        X = SimpleMapping[str, Any]
        self.assertEqual(X.__parameters__, ())
        with self.assertRaises(TypeError):
            X[unicode]
        with self.assertRaises(TypeError):
            X[unicode, unicode]
        Y = SimpleMapping[XK, unicode]
        self.assertEqual(Y.__parameters__, (XK,))
        Y[unicode]
        with self.assertRaises(TypeError):
            Y[unicode, unicode]

    def test_generic_errors(self):
        with self.assertRaises(TypeError):
            isinstance([], List[int])
        with self.assertRaises(TypeError):
            issubclass(list, List[int])

    def test_init(self):
        T = TypeVar('T')
        S = TypeVar('S')
        with self.assertRaises(TypeError):
            Generic[T, T]
        with self.assertRaises(TypeError):
            Generic[T, S, T]

    def test_repr(self):
        self.assertEqual(repr(SimpleMapping),
                         __name__ + '.' + 'SimpleMapping')
        self.assertEqual(repr(MySimpleMapping),
                         __name__ + '.' + 'MySimpleMapping')

    def test_chain_repr(self):
        T = TypeVar('T')
        S = TypeVar('S')

        class C(Generic[T]):
            pass

        X = C[Tuple[S, T]]
        self.assertEqual(X, C[Tuple[S, T]])
        self.assertNotEqual(X, C[Tuple[T, S]])

        Y = X[T, int]
        self.assertEqual(Y, X[T, int])
        self.assertNotEqual(Y, X[S, int])
        self.assertNotEqual(Y, X[T, str])

        Z = Y[str]
        self.assertEqual(Z, Y[str])
        self.assertNotEqual(Z, Y[int])
        self.assertNotEqual(Z, Y[T])

        self.assertTrue(str(Z).endswith(
            '.C[typing.Tuple[str, int]]'))

    def test_new_repr(self):
        T = TypeVar('T')
        U = TypeVar('U', covariant=True)
        S = TypeVar('S')

        self.assertEqual(repr(List), 'typing.List')
        self.assertEqual(repr(List[T]), 'typing.List[~T]')
        self.assertEqual(repr(List[U]), 'typing.List[+U]')
        self.assertEqual(repr(List[S][T][int]), 'typing.List[int]')
        self.assertEqual(repr(List[int]), 'typing.List[int]')

    def test_new_repr_complex(self):
        T = TypeVar('T')
        TS = TypeVar('TS')

        self.assertEqual(repr(typing.Mapping[T, TS][TS, T]), 'typing.Mapping[~TS, ~T]')
        self.assertEqual(repr(List[Tuple[T, TS]][int, T]),
                         'typing.List[typing.Tuple[int, ~T]]')
        self.assertEqual(repr(List[Tuple[T, T]][List[int]]),
                 'typing.List[typing.Tuple[typing.List[int], typing.List[int]]]')

    def test_new_repr_bare(self):
        T = TypeVar('T')
        self.assertEqual(repr(Generic[T]), 'typing.Generic[~T]')
        self.assertEqual(repr(typing._Protocol[T]), 'typing.Protocol[~T]')
        class C(typing.Dict[Any, Any]): pass
        # this line should just work
        repr(C.__mro__)

    def test_dict(self):
        T = TypeVar('T')

        class B(Generic[T]):
            pass

        b = B()
        b.foo = 42
        self.assertEqual(b.__dict__, {'foo': 42})

        class C(B[int]):
            pass

        c = C()
        c.bar = 'abc'
        self.assertEqual(c.__dict__, {'bar': 'abc'})

    def test_false_subclasses(self):
        class MyMapping(MutableMapping[str, str]): pass
        self.assertNotIsInstance({}, MyMapping)
        self.assertNotIsSubclass(dict, MyMapping)

    def test_abc_bases(self):
        class MM(MutableMapping[str, str]):
            def __getitem__(self, k):
                return None
            def __setitem__(self, k, v):
                pass
            def __delitem__(self, k):
                pass
            def __iter__(self):
                return iter(())
            def __len__(self):
                return 0
        # this should just work
        MM().update()
        self.assertIsInstance(MM(), collections_abc.MutableMapping)
        self.assertIsInstance(MM(), MutableMapping)
        self.assertNotIsInstance(MM(), List)
        self.assertNotIsInstance({}, MM)

    def test_multiple_bases(self):
        class MM1(MutableMapping[str, str], collections_abc.MutableMapping):
            pass
        with self.assertRaises(TypeError):
            # consistent MRO not possible
            class MM2(collections_abc.MutableMapping, MutableMapping[str, str]):
                pass

    def test_orig_bases(self):
        T = TypeVar('T')
        class C(typing.Dict[str, T]): pass
        self.assertEqual(C.__orig_bases__, (typing.Dict[str, T],))

    def test_naive_runtime_checks(self):
        def naive_dict_check(obj, tp):
            # Check if a dictionary conforms to Dict type
            if len(tp.__parameters__) > 0:
                raise NotImplementedError
            if tp.__args__:
                KT, VT = tp.__args__
                return all(isinstance(k, KT) and isinstance(v, VT)
                   for k, v in obj.items())
        self.assertTrue(naive_dict_check({'x': 1}, typing.Dict[typing.Text, int]))
        self.assertFalse(naive_dict_check({1: 'x'}, typing.Dict[typing.Text, int]))
        with self.assertRaises(NotImplementedError):
            naive_dict_check({1: 'x'}, typing.Dict[typing.Text, T])

        def naive_generic_check(obj, tp):
            # Check if an instance conforms to the generic class
            if not hasattr(obj, '__orig_class__'):
                raise NotImplementedError
            return obj.__orig_class__ == tp
        class Node(Generic[T]): pass
        self.assertTrue(naive_generic_check(Node[int](), Node[int]))
        self.assertFalse(naive_generic_check(Node[str](), Node[int]))
        self.assertFalse(naive_generic_check(Node[str](), List))
        with self.assertRaises(NotImplementedError):
            naive_generic_check([1,2,3], Node[int])

        def naive_list_base_check(obj, tp):
            # Check if list conforms to a List subclass
            return all(isinstance(x, tp.__orig_bases__[0].__args__[0])
                       for x in obj)
        class C(List[int]): pass
        self.assertTrue(naive_list_base_check([1, 2, 3], C))
        self.assertFalse(naive_list_base_check(['a', 'b'], C))

    def test_multi_subscr_base(self):
        T = TypeVar('T')
        U = TypeVar('U')
        V = TypeVar('V')
        class C(List[T][U][V]): pass
        class D(C, List[T][U][V]): pass
        self.assertEqual(C.__parameters__, (V,))
        self.assertEqual(D.__parameters__, (V,))
        self.assertEqual(C[int].__parameters__, ())
        self.assertEqual(D[int].__parameters__, ())
        self.assertEqual(C[int].__args__, (int,))
        self.assertEqual(D[int].__args__, (int,))
        self.assertEqual(C.__bases__, (List,))
        self.assertEqual(D.__bases__, (C, List))
        self.assertEqual(C.__orig_bases__, (List[T][U][V],))
        self.assertEqual(D.__orig_bases__, (C, List[T][U][V]))

    def test_pickle(self):
        global C  # pickle wants to reference the class by name
        T = TypeVar('T')

        class B(Generic[T]):
            pass

        class C(B[int]):
            pass

        c = C()
        c.foo = 42
        c.bar = 'abc'
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(c, proto)
            x = pickle.loads(z)
            self.assertEqual(x.foo, 42)
            self.assertEqual(x.bar, 'abc')
            self.assertEqual(x.__dict__, {'foo': 42, 'bar': 'abc'})

    def test_errors(self):
        with self.assertRaises(TypeError):
            B = SimpleMapping[XK, Any]

            class C(Generic[B]):
                pass

    def test_repr_2(self):
        PY32 = sys.version_info[:2] < (3, 3)

        class C(Generic[T]):
            pass

        self.assertEqual(C.__module__, __name__)
        if not PY32:
            self.assertEqual(C.__qualname__,
                             'GenericTests.test_repr_2.<locals>.C')
        self.assertEqual(repr(C).split('.')[-1], 'C')
        X = C[int]
        self.assertEqual(X.__module__, __name__)
        if not PY32:
            self.assertEqual(X.__qualname__, 'C')
        self.assertEqual(repr(X).split('.')[-1], 'C[int]')

        class Y(C[int]):
            pass

        self.assertEqual(Y.__module__, __name__)
        if not PY32:
            self.assertEqual(Y.__qualname__,
                             'GenericTests.test_repr_2.<locals>.Y')
        self.assertEqual(repr(Y).split('.')[-1], 'Y')

    def test_eq_1(self):
        self.assertEqual(Generic, Generic)
        self.assertEqual(Generic[T], Generic[T])
        self.assertNotEqual(Generic[KT], Generic[VT])

    def test_eq_2(self):

        class A(Generic[T]):
            pass

        class B(Generic[T]):
            pass

        self.assertEqual(A, A)
        self.assertNotEqual(A, B)
        self.assertEqual(A[T], A[T])
        self.assertNotEqual(A[T], B[T])

    def test_multiple_inheritance(self):

        class A(Generic[T, VT]):
            pass

        class B(Generic[KT, T]):
            pass

        class C(A[T, VT], Generic[VT, T, KT], B[KT, T]):
            pass

        self.assertEqual(C.__parameters__, (VT, T, KT))

    def test_nested(self):

        G = Generic

        class Visitor(G[T]):

            a = None

            def set(self, a):
                self.a = a

            def get(self):
                return self.a

            def visit(self):
                return self.a

        V = Visitor[typing.List[int]]

        class IntListVisitor(V):

            def append(self, x):
                self.a.append(x)

        a = IntListVisitor()
        a.set([])
        a.append(1)
        a.append(42)
        self.assertEqual(a.get(), [1, 42])

    def test_type_erasure(self):
        T = TypeVar('T')

        class Node(Generic[T]):
            def __init__(self, label,
                         left = None,
                         right = None):
                self.label = label  # type: T
                self.left = left  # type: Optional[Node[T]]
                self.right = right  # type: Optional[Node[T]]

        def foo(x):
            a = Node(x)
            b = Node[T](x)
            c = Node[Any](x)
            self.assertIs(type(a), Node)
            self.assertIs(type(b), Node)
            self.assertIs(type(c), Node)
            self.assertEqual(a.label, x)
            self.assertEqual(b.label, x)
            self.assertEqual(c.label, x)

        foo(42)

    def test_implicit_any(self):
        T = TypeVar('T')

        class C(Generic[T]):
            pass

        class D(C):
            pass

        self.assertEqual(D.__parameters__, ())

        with self.assertRaises(Exception):
            D[int]
        with self.assertRaises(Exception):
            D[Any]
        with self.assertRaises(Exception):
            D[T]

class ClassVarTests(BaseTestCase):

    def test_basics(self):
        with self.assertRaises(TypeError):
            ClassVar[1]
        with self.assertRaises(TypeError):
            ClassVar[int, str]
        with self.assertRaises(TypeError):
            ClassVar[int][str]

    def test_repr(self):
        self.assertEqual(repr(ClassVar), 'typing.ClassVar')
        cv = ClassVar[int]
        self.assertEqual(repr(cv), 'typing.ClassVar[int]')
        cv = ClassVar[Employee]
        self.assertEqual(repr(cv), 'typing.ClassVar[%s.Employee]' % __name__)

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError):
            class C(type(ClassVar)):
                pass
        with self.assertRaises(TypeError):
            class C(type(ClassVar[int])):
                pass

    def test_cannot_init(self):
        with self.assertRaises(TypeError):
            ClassVar()
        with self.assertRaises(TypeError):
            type(ClassVar)()
        with self.assertRaises(TypeError):
            type(ClassVar[Optional[int]])()

    def test_no_isinstance(self):
        with self.assertRaises(TypeError):
            isinstance(1, ClassVar[int])
        with self.assertRaises(TypeError):
            issubclass(int, ClassVar)


class CastTests(BaseTestCase):

    def test_basics(self):
        self.assertEqual(cast(int, 42), 42)
        self.assertEqual(cast(float, 42), 42)
        self.assertIs(type(cast(float, 42)), int)
        self.assertEqual(cast(Any, 42), 42)
        self.assertEqual(cast(list, 42), 42)
        self.assertEqual(cast(Union[str, float], 42), 42)
        self.assertEqual(cast(AnyStr, 42), 42)
        self.assertEqual(cast(None, 42), 42)

    def test_errors(self):
        # Bogus calls are not expected to fail.
        cast(42, 42)
        cast('hello', 42)


class ForwardRefTests(BaseTestCase):

    def test_forwardref_instance_type_error(self):
        fr = typing._ForwardRef('int')
        with self.assertRaises(TypeError):
            isinstance(42, fr)

    def test_syntax_error(self):

        with self.assertRaises(SyntaxError):
            Generic['/T']


class OverloadTests(BaseTestCase):

    def test_overload_exists(self):
        from typing import overload

    def test_overload_fails(self):
        from typing import overload

        with self.assertRaises(RuntimeError):

            @overload
            def blah():
                pass

            blah()

    def test_overload_succeeds(self):
        from typing import overload

        @overload
        def blah():
            pass

        def blah():
            pass

        blah()


class CollectionsAbcTests(BaseTestCase):

    def test_hashable(self):
        self.assertIsInstance(42, typing.Hashable)
        self.assertNotIsInstance([], typing.Hashable)

    def test_iterable(self):
        self.assertIsInstance([], typing.Iterable)
        # Due to ABC caching, the second time takes a separate code
        # path and could fail.  So call this a few times.
        self.assertIsInstance([], typing.Iterable)
        self.assertIsInstance([], typing.Iterable)
        self.assertNotIsInstance(42, typing.Iterable)
        # Just in case, also test issubclass() a few times.
        self.assertIsSubclass(list, typing.Iterable)
        self.assertIsSubclass(list, typing.Iterable)

    def test_iterator(self):
        it = iter([])
        self.assertIsInstance(it, typing.Iterator)
        self.assertNotIsInstance(42, typing.Iterator)

    def test_sized(self):
        self.assertIsInstance([], typing.Sized)
        self.assertNotIsInstance(42, typing.Sized)

    def test_container(self):
        self.assertIsInstance([], typing.Container)
        self.assertNotIsInstance(42, typing.Container)

    def test_abstractset(self):
        self.assertIsInstance(set(), typing.AbstractSet)
        self.assertNotIsInstance(42, typing.AbstractSet)

    def test_mutableset(self):
        self.assertIsInstance(set(), typing.MutableSet)
        self.assertNotIsInstance(frozenset(), typing.MutableSet)

    def test_mapping(self):
        self.assertIsInstance({}, typing.Mapping)
        self.assertNotIsInstance(42, typing.Mapping)

    def test_mutablemapping(self):
        self.assertIsInstance({}, typing.MutableMapping)
        self.assertNotIsInstance(42, typing.MutableMapping)

    def test_sequence(self):
        self.assertIsInstance([], typing.Sequence)
        self.assertNotIsInstance(42, typing.Sequence)

    def test_mutablesequence(self):
        self.assertIsInstance([], typing.MutableSequence)
        self.assertNotIsInstance((), typing.MutableSequence)

    def test_bytestring(self):
        self.assertIsInstance(b'', typing.ByteString)
        self.assertIsInstance(bytearray(b''), typing.ByteString)

    def test_list(self):
        self.assertIsSubclass(list, typing.List)

    def test_set(self):
        self.assertIsSubclass(set, typing.Set)
        self.assertNotIsSubclass(frozenset, typing.Set)

    def test_frozenset(self):
        self.assertIsSubclass(frozenset, typing.FrozenSet)
        self.assertNotIsSubclass(set, typing.FrozenSet)

    def test_dict(self):
        self.assertIsSubclass(dict, typing.Dict)

    def test_no_list_instantiation(self):
        with self.assertRaises(TypeError):
            typing.List()
        with self.assertRaises(TypeError):
            typing.List[T]()
        with self.assertRaises(TypeError):
            typing.List[int]()

    def test_list_subclass(self):

        class MyList(typing.List[int]):
            pass

        a = MyList()
        self.assertIsInstance(a, MyList)
        self.assertIsInstance(a, typing.Sequence)

        self.assertIsSubclass(MyList, list)
        self.assertNotIsSubclass(list, MyList)

    def test_no_dict_instantiation(self):
        with self.assertRaises(TypeError):
            typing.Dict()
        with self.assertRaises(TypeError):
            typing.Dict[KT, VT]()
        with self.assertRaises(TypeError):
            typing.Dict[str, int]()

    def test_dict_subclass(self):

        class MyDict(typing.Dict[str, int]):
            pass

        d = MyDict()
        self.assertIsInstance(d, MyDict)
        self.assertIsInstance(d, typing.MutableMapping)

        self.assertIsSubclass(MyDict, dict)
        self.assertNotIsSubclass(dict, MyDict)

    def test_no_defaultdict_instantiation(self):
        with self.assertRaises(TypeError):
            typing.DefaultDict()
        with self.assertRaises(TypeError):
            typing.DefaultDict[KT, VT]()
        with self.assertRaises(TypeError):
            typing.DefaultDict[str, int]()

    def test_defaultdict_subclass(self):

        class MyDefDict(typing.DefaultDict[str, int]):
            pass

        dd = MyDefDict()
        self.assertIsInstance(dd, MyDefDict)

        self.assertIsSubclass(MyDefDict, collections.defaultdict)
        self.assertNotIsSubclass(collections.defaultdict, MyDefDict)

    def test_no_set_instantiation(self):
        with self.assertRaises(TypeError):
            typing.Set()
        with self.assertRaises(TypeError):
            typing.Set[T]()
        with self.assertRaises(TypeError):
            typing.Set[int]()

    def test_set_subclass_instantiation(self):

        class MySet(typing.Set[int]):
            pass

        d = MySet()
        self.assertIsInstance(d, MySet)

    def test_no_frozenset_instantiation(self):
        with self.assertRaises(TypeError):
            typing.FrozenSet()
        with self.assertRaises(TypeError):
            typing.FrozenSet[T]()
        with self.assertRaises(TypeError):
            typing.FrozenSet[int]()

    def test_frozenset_subclass_instantiation(self):

        class MyFrozenSet(typing.FrozenSet[int]):
            pass

        d = MyFrozenSet()
        self.assertIsInstance(d, MyFrozenSet)

    def test_no_tuple_instantiation(self):
        with self.assertRaises(TypeError):
            Tuple()
        with self.assertRaises(TypeError):
            Tuple[T]()
        with self.assertRaises(TypeError):
            Tuple[int]()

    def test_generator(self):
        def foo():
            yield 42
        g = foo()
        self.assertIsSubclass(type(g), typing.Generator)

    def test_no_generator_instantiation(self):
        with self.assertRaises(TypeError):
            typing.Generator()
        with self.assertRaises(TypeError):
            typing.Generator[T, T, T]()
        with self.assertRaises(TypeError):
            typing.Generator[int, int, int]()

    def test_subclassing(self):

        class MMA(typing.MutableMapping):
            pass

        with self.assertRaises(TypeError):  # It's abstract
            MMA()

        class MMC(MMA):
            def __getitem__(self, k):
                return None
            def __setitem__(self, k, v):
                pass
            def __delitem__(self, k):
                pass
            def __iter__(self):
                return iter(())
            def __len__(self):
                return 0

        self.assertEqual(len(MMC()), 0)
        assert callable(MMC.update)
        self.assertIsInstance(MMC(), typing.Mapping)

        class MMB(typing.MutableMapping[KT, VT]):
            def __getitem__(self, k):
                return None
            def __setitem__(self, k, v):
                pass
            def __delitem__(self, k):
                pass
            def __iter__(self):
                return iter(())
            def __len__(self):
                return 0

        self.assertEqual(len(MMB()), 0)
        self.assertEqual(len(MMB[str, str]()), 0)
        self.assertEqual(len(MMB[KT, VT]()), 0)

        self.assertNotIsSubclass(dict, MMA)
        self.assertNotIsSubclass(dict, MMB)

        self.assertIsSubclass(MMA, typing.Mapping)
        self.assertIsSubclass(MMB, typing.Mapping)
        self.assertIsSubclass(MMC, typing.Mapping)

        self.assertIsInstance(MMB[KT, VT](), typing.Mapping)
        self.assertIsInstance(MMB[KT, VT](), collections.Mapping)

        self.assertIsSubclass(MMA, collections.Mapping)
        self.assertIsSubclass(MMB, collections.Mapping)
        self.assertIsSubclass(MMC, collections.Mapping)

        self.assertIsSubclass(MMB[str, str], typing.Mapping)
        self.assertIsSubclass(MMC, MMA)

        class I(typing.Iterable): pass
        self.assertNotIsSubclass(list, I)

        class G(typing.Generator[int, int, int]): pass
        def g(): yield 0
        self.assertIsSubclass(G, typing.Generator)
        self.assertIsSubclass(G, typing.Iterable)
        if hasattr(collections, 'Generator'):
            self.assertIsSubclass(G, collections.Generator)
        self.assertIsSubclass(G, collections.Iterable)
        self.assertNotIsSubclass(type(g), G)

    def test_subclassing_subclasshook(self):

        class Base(typing.Iterable):
            @classmethod
            def __subclasshook__(cls, other):
                if other.__name__ == 'Foo':
                    return True
                else:
                    return False

        class C(Base): pass
        class Foo: pass
        class Bar: pass
        self.assertIsSubclass(Foo, Base)
        self.assertIsSubclass(Foo, C)
        self.assertNotIsSubclass(Bar, C)

    def test_subclassing_register(self):

        class A(typing.Container): pass
        class B(A): pass

        class C: pass
        A.register(C)
        self.assertIsSubclass(C, A)
        self.assertNotIsSubclass(C, B)

        class D: pass
        B.register(D)
        self.assertIsSubclass(D, A)
        self.assertIsSubclass(D, B)

        class M(): pass
        collections.MutableMapping.register(M)
        self.assertIsSubclass(M, typing.Mapping)

    def test_collections_as_base(self):

        class M(collections.Mapping): pass
        self.assertIsSubclass(M, typing.Mapping)
        self.assertIsSubclass(M, typing.Iterable)

        class S(collections.MutableSequence): pass
        self.assertIsSubclass(S, typing.MutableSequence)
        self.assertIsSubclass(S, typing.Iterable)

        class I(collections.Iterable): pass
        self.assertIsSubclass(I, typing.Iterable)

        class A(collections.Mapping): pass
        class B: pass
        A.register(B)
        self.assertIsSubclass(B, typing.Mapping)

class TypeTests(BaseTestCase):

    def test_type_basic(self):

        class User(object): pass
        class BasicUser(User): pass
        class ProUser(User): pass

        def new_user(user_class):
            # type: (Type[User]) -> User
            return user_class()

        joe = new_user(BasicUser)

    def test_type_typevar(self):

        class User(object): pass
        class BasicUser(User): pass
        class ProUser(User): pass

        global U
        U = TypeVar('U', bound=User)

        def new_user(user_class):
            # type: (Type[U]) -> U
            return user_class()

        joe = new_user(BasicUser)

    def test_type_optional(self):
        A = Optional[Type[BaseException]]

        def foo(a):
            # type: (A) -> Optional[BaseException]
            if a is None:
                return None
            else:
                return a()

        assert isinstance(foo(KeyboardInterrupt), KeyboardInterrupt)
        assert foo(None) is None


class NewTypeTests(BaseTestCase):

    def test_basic(self):
        UserId = NewType('UserId', int)
        UserName = NewType('UserName', str)
        self.assertIsInstance(UserId(5), int)
        self.assertIsInstance(UserName('Joe'), type('Joe'))
        self.assertEqual(UserId(5) + 1, 6)

    def test_errors(self):
        UserId = NewType('UserId', int)
        UserName = NewType('UserName', str)
        with self.assertRaises(TypeError):
            issubclass(UserId, int)
        with self.assertRaises(TypeError):
            class D(UserName):
                pass


class NamedTupleTests(BaseTestCase):

    def test_basics(self):
        Emp = NamedTuple('Emp', [('name', str), ('id', int)])
        self.assertIsSubclass(Emp, tuple)
        joe = Emp('Joe', 42)
        jim = Emp(name='Jim', id=1)
        self.assertIsInstance(joe, Emp)
        self.assertIsInstance(joe, tuple)
        self.assertEqual(joe.name, 'Joe')
        self.assertEqual(joe.id, 42)
        self.assertEqual(jim.name, 'Jim')
        self.assertEqual(jim.id, 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp._fields, ('name', 'id'))
        self.assertEqual(Emp._field_types, dict(name=str, id=int))

    def test_pickle(self):
        global Emp  # pickle wants to reference the class by name
        Emp = NamedTuple('Emp', [('name', str), ('id', int)])
        jane = Emp('jane', 37)
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(jane, proto)
            jane2 = pickle.loads(z)
            self.assertEqual(jane2, jane)


class IOTests(BaseTestCase):

    def test_io_submodule(self):
        from typing.io import IO, TextIO, BinaryIO, __all__, __name__
        self.assertIs(IO, typing.IO)
        self.assertIs(TextIO, typing.TextIO)
        self.assertIs(BinaryIO, typing.BinaryIO)
        self.assertEqual(set(__all__), set(['IO', 'TextIO', 'BinaryIO']))
        self.assertEqual(__name__, 'typing.io')


class RETests(BaseTestCase):
    # Much of this is really testing _TypeAlias.

    def test_basics(self):
        pat = re.compile('[a-z]+', re.I)
        self.assertIsSubclass(pat.__class__, Pattern)
        self.assertIsSubclass(type(pat), Pattern)
        self.assertIsInstance(pat, Pattern)

        mat = pat.search('12345abcde.....')
        self.assertIsSubclass(mat.__class__, Match)
        self.assertIsSubclass(type(mat), Match)
        self.assertIsInstance(mat, Match)

        # these should just work
        p = Pattern[Union[str, bytes]]
        m = Match[Union[bytes, str]]

    def test_errors(self):
        with self.assertRaises(TypeError):
            # Doesn't fit AnyStr.
            Pattern[int]
        with self.assertRaises(TypeError):
            # Can't change type vars?
            Match[T]
        m = Match[Union[str, bytes]]
        with self.assertRaises(TypeError):
            # Too complicated?
            m[str]
        with self.assertRaises(TypeError):
            # We don't support isinstance().
            isinstance(42, Pattern[str])

    def test_repr(self):
        self.assertEqual(repr(Pattern), 'Pattern[~AnyStr]')
        self.assertEqual(repr(Pattern[unicode]), 'Pattern[unicode]')
        self.assertEqual(repr(Pattern[str]), 'Pattern[str]')
        self.assertEqual(repr(Match), 'Match[~AnyStr]')
        self.assertEqual(repr(Match[unicode]), 'Match[unicode]')
        self.assertEqual(repr(Match[str]), 'Match[str]')

    def test_re_submodule(self):
        from typing.re import Match, Pattern, __all__, __name__
        self.assertIs(Match, typing.Match)
        self.assertIs(Pattern, typing.Pattern)
        self.assertEqual(set(__all__), set(['Match', 'Pattern']))
        self.assertEqual(__name__, 'typing.re')

    def test_cannot_subclass(self):
        with self.assertRaises(TypeError) as ex:

            class A(typing.Match):
                pass

        self.assertEqual(str(ex.exception),
                         "Cannot subclass typing._TypeAlias")


class AllTests(BaseTestCase):
    """Tests for __all__."""

    def test_all(self):
        from typing import __all__ as a
        # Just spot-check the first and last of every category.
        self.assertIn('AbstractSet', a)
        self.assertIn('ValuesView', a)
        self.assertIn('cast', a)
        self.assertIn('overload', a)
        # Check that io and re are not exported.
        self.assertNotIn('io', a)
        self.assertNotIn('re', a)
        # Spot-check that stdlib modules aren't exported.
        self.assertNotIn('os', a)
        self.assertNotIn('sys', a)
        # Check that Text is defined.
        self.assertIn('Text', a)

    def test_respect_no_type_check(self):
        @typing.no_type_check
        class NoTpCheck(object):
            class Inn(object):
                def __init__(self, x): pass
                    # type: (this is not actualy a type) -> None
        self.assertTrue(NoTpCheck.__no_type_check__)
        self.assertTrue(NoTpCheck.Inn.__init__.__no_type_check__)

    def test_get_type_hints_dummy(self):

        def foo(x):
            # type: (int) -> int
            return x + 1

        self.assertIsNone(typing.get_type_hints(foo))


if __name__ == '__main__':
    main()
