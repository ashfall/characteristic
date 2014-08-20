from __future__ import absolute_import, division, print_function

import sys

import pytest

from characteristic import (
    Attribute,
    NOTHING,
    _ensure_attributes,
    attributes,
    immutable,
    with_cmp,
    with_init,
    with_repr,
)

PY2 = sys.version_info[0] == 2


class TestAttribute(object):
    def test_init_simple(self):
        """
        Instantiating with just the name initializes properly.
        """
        a = Attribute("foo")
        assert "foo" == a.name
        assert NOTHING is a._default

    def test_init_default_factory(self):
        """
        Instantiating with default_factory creates a proper descriptor for
        _default.
        """
        a = Attribute("foo", default_factory=list)
        assert list() == a._default

    def test_init_default_value(self):
        """
        Instantiating with default_value initializes default properly.
        """
        a = Attribute("foo", default_value="bar")
        assert "bar" == a._default

    def test_ambiguous_defaults(self):
        """
        Instantiating with both default_value and default_factory raises
        ValueError.
        """
        with pytest.raises(ValueError):
            Attribute(
                "foo",
                default_value="bar",
                default_factory=lambda: 42
            )

    def test_missing_attr(self):
        """
        Accessing inexistent attributes still raises an AttributeError.
        """
        a = Attribute("foo")
        with pytest.raises(AttributeError):
            a.bar

    def test_alias(self):
        """
        If an attribute with a leading _ is defined, the initializer keyword
        is stripped of it.
        """
        a = Attribute("_private")
        assert "private" == a._kw_name

    def test_non_alias(self):
        """
        The keyword name of a non-private
        """
        a = Attribute("public")
        assert "public" == a._kw_name

    def test_dunder(self):
        """
        Dunder gets all _ stripped.
        """
        a = Attribute("__very_private")
        assert "very_private" == a._kw_name

    def test_keep_underscores(self):
        """
        No aliasing if keep_underscores is True.
        """
        a = Attribute("_private", keep_underscores=True)
        assert a.name == a._kw_name

    def test_repr(self):
        """
        repr returns the correct string.
        """
        a = Attribute(
            name="name",
            exclude_from_cmp=True,
            exclude_from_init=True,
            exclude_from_repr=True,
            exclude_from_immutable=True,
            default_value=42,
            instance_of=str,
            keep_underscores=True
        )
        assert (
            "<Attribute(name='name', exclude_from_cmp=True, "
            "exclude_from_init=True, exclude_from_repr=True, "
            "exclude_from_immutable=True, "
            "default_value=42, default_factory=None, instance_of=<{0} 'str'>,"
            " keep_underscores=True)>"
        ).format("type" if PY2 else "class") == repr(a)


@with_cmp(["a", "b"])
class CmpC(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b


class TestWithCmp(object):
    def test_equal(self):
        """
        Equal objects are detected as equal.
        """
        assert CmpC(1, 2) == CmpC(1, 2)
        assert not (CmpC(1, 2) != CmpC(1, 2))

    def test_unequal_same_class(self):
        """
        Unequal objects of correct type are detected as unequal.
        """
        assert CmpC(1, 2) != CmpC(2, 1)
        assert not (CmpC(1, 2) == CmpC(2, 1))

    def test_unequal_different_class(self):
        """
        Unequal objects of differnt type are detected even if their attributes
        match.
        """
        class NotCmpC(object):
            a = 1
            b = 2
        assert CmpC(1, 2) != NotCmpC()
        assert not (CmpC(1, 2) == NotCmpC())

    def test_lt(self):
        """
        __lt__ compares objects as tuples of attribute values.
        """
        for a, b in [
            ((1, 2),  (2, 1)),
            ((1, 2),  (1, 3)),
            (("a", "b"), ("b", "a")),
        ]:
            assert CmpC(*a) < CmpC(*b)

    def test_lt_unordable(self):
        """
        __lt__ returns NotImplemented if classes differ.
        """
        assert NotImplemented == (CmpC(1, 2).__lt__(42))

    def test_le(self):
        """
        __le__ compares objects as tuples of attribute values.
        """
        for a, b in [
            ((1, 2),  (2, 1)),
            ((1, 2),  (1, 3)),
            ((1, 1),  (1, 1)),
            (("a", "b"), ("b", "a")),
            (("a", "b"), ("a", "b")),
        ]:
            assert CmpC(*a) <= CmpC(*b)

    def test_le_unordable(self):
        """
        __le__ returns NotImplemented if classes differ.
        """
        assert NotImplemented == (CmpC(1, 2).__le__(42))

    def test_gt(self):
        """
        __gt__ compares objects as tuples of attribute values.
        """
        for a, b in [
            ((2, 1), (1, 2)),
            ((1, 3), (1, 2)),
            (("b", "a"), ("a", "b")),
        ]:
            assert CmpC(*a) > CmpC(*b)

    def test_gt_unordable(self):
        """
        __gt__ returns NotImplemented if classes differ.
        """
        assert NotImplemented == (CmpC(1, 2).__gt__(42))

    def test_ge(self):
        """
        __ge__ compares objects as tuples of attribute values.
        """
        for a, b in [
            ((2, 1), (1, 2)),
            ((1, 3), (1, 2)),
            ((1, 1), (1, 1)),
            (("b", "a"), ("a", "b")),
            (("a", "b"), ("a", "b")),
        ]:
            assert CmpC(*a) >= CmpC(*b)

    def test_ge_unordable(self):
        """
        __ge__ returns NotImplemented if classes differ.
        """
        assert NotImplemented == (CmpC(1, 2).__ge__(42))

    def test_hash(self):
        """
        __hash__ returns different hashes for different values.
        """
        assert hash(CmpC(1, 2)) != hash(CmpC(1, 1))

    def test_Attribute_exclude_from_cmp(self):
        """
        Ignores attribute if exclude_from_cmp=True.
        """
        @with_cmp([Attribute("a", exclude_from_cmp=True), "b"])
        class C(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        assert C(42, 1) == C(23, 1)


@with_repr(["a", "b"])
class ReprC(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b


class TestReprAttrs(object):
    def test_repr(self):
        """
        Test repr returns a sensible value.
        """
        assert "<ReprC(a=1, b=2)>" == repr(ReprC(1, 2))

    def test_Attribute_exclude_from_repr(self):
        """
        Ignores attribute if exclude_from_repr=True.
        """
        @with_repr([Attribute("a", exclude_from_repr=True), "b"])
        class C(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        assert "<C(b=2)>" == repr(C(1, 2))


@with_init([Attribute("a"), Attribute("b")])
class InitC(object):
    def __init__(self):
        if self.a == self.b:
            raise ValueError


class TestWithInit(object):
    def test_sets_attributes(self):
        """
        The attributes are initialized using the passed keywords.
        """
        obj = InitC(a=1, b=2)
        assert 1 == obj.a
        assert 2 == obj.b

    def test_custom_init(self):
        """
        The class initializer is called too.
        """
        with pytest.raises(ValueError):
            InitC(a=1, b=1)

    def test_passes_args(self):
        """
        All positional parameters are passed to the original initializer.
        """
        @with_init(["a"])
        class InitWithArg(object):
            def __init__(self, arg):
                self.arg = arg

        obj = InitWithArg(42, a=1)
        assert 42 == obj.arg
        assert 1 == obj.a

    def test_passes_remaining_kw(self):
        """
        Keyword arguments that aren't used for attributes are passed to the
        original initializer.
        """
        @with_init(["a"])
        class InitWithKWArg(object):
            def __init__(self, kw_arg=None):
                self.kw_arg = kw_arg

        obj = InitWithKWArg(a=1, kw_arg=42)
        assert 42 == obj.kw_arg
        assert 1 == obj.a

    def test_does_not_pass_attrs(self):
        """
        The attributes are removed from the keyword arguments before they are
        passed to the original initializer.
        """
        @with_init(["a"])
        class InitWithKWArgs(object):
            def __init__(self, **kw):
                assert "a" not in kw
                assert "b" in kw
        InitWithKWArgs(a=1, b=42)

    def test_defaults(self):
        """
        If defaults are passed, they are used as fallback.
        """
        @with_init(["a", "b"], defaults={"b": 2})
        class InitWithDefaults(object):
            pass
        obj = InitWithDefaults(a=1)
        assert 2 == obj.b

    def test_missing_arg(self):
        """
        Raises `ValueError` if a value isn't passed.
        """
        with pytest.raises(ValueError) as e:
            InitC(a=1)
        assert "Missing keyword value for 'b'." == e.value.args[0]

    def test_defaults_conflict(self):
        """
        Raises `ValueError` if both defaults and an Attribute are passed.
        """
        with pytest.raises(ValueError) as e:
            @with_init([Attribute("a")], defaults={"a": 42})
            class C(object):
                pass
        assert (
            "Mixing of the 'defaults' keyword argument and passing instances "
            "of Attribute for 'attrs' is prohibited.  Please don't use "
            "'defaults' anymore, it has been deprecated in 14.0."
            == e.value.args[0]
        )

    def test_attribute(self):
        """
        String attributes are converted to Attributes and thus work.
        """
        @with_init(["a"])
        class C(object):
            pass
        o = C(a=1)
        assert 1 == o.a

    def test_default_factory(self):
        """
        The default factory is used for each instance of missing keyword
        argument.
        """
        @with_init([Attribute("a", default_factory=list)])
        class C(object):
            pass
        o1 = C()
        o2 = C()
        assert o1.a is not o2.a

    def test_optimizes(self):
        """
        Uses __original_setattr__ if possible.
        """
        @immutable(["a"])
        @with_init(["a"])
        class C(object):
            pass

        c = C(a=42)
        assert c.__original_setattr__ == c.__characteristic_setattr__

    def test_setattr(self):
        """
        Uses setattr by default.
        """
        @with_init(["a"])
        class C(object):
            pass

        c = C(a=42)
        assert c.__setattr__ == c.__characteristic_setattr__

    def test_underscores(self):
        """
        with_init takes keyword aliasing into account.
        """
        @with_init([Attribute("_a")])
        class C(object):
            pass
        c = C(a=1)
        assert 1 == c._a

    def test_plain_no_alias(self):
        """
        str-based attributes don't get aliased for backward-compatibility.
        """
        @with_init(["_a"])
        class C(object):
            pass
        c = C(_a=1)
        assert 1 == c._a

    def test_instance_of_fail(self):
        """
        Raise `TypeError` if an Attribute with an `instance_of` is is attempted
        to be set to a mismatched type.
        """
        @with_init([Attribute("a", instance_of=int)])
        class C(object):
            pass
        with pytest.raises(TypeError) as e:
            C(a="not an int!")
        assert (
            "Attribute 'a' must be an instance of 'int'."
            == e.value.args[0]
        )

    def test_instance_of_success(self):
        """
        Setting an attribute to a value that doesn't conflict with an
        `instance_of` declaration works.
        """
        @with_init([Attribute("a", instance_of=int)])
        class C(object):
            pass
        c = C(a=42)
        assert 42 == c.a

    def test_Attribute_exclude_from_init(self):
        """
        Ignores attribute if exclude_from_init=True.
        """
        @with_init([Attribute("a", exclude_from_init=True), "b"])
        class C(object):
            pass

        C(b=1)


@attributes(["a", "b"], create_init=True)
class MagicWithInitC(object):
    pass


@attributes(["a", "b"], create_init=False)
class MagicWithoutInitC(object):
    pass


class TestAttributes(object):
    def test_leaves_init_alone(self):
        """
        If *create_init* is `False`, leave __init__ alone.
        """
        obj = MagicWithoutInitC()
        with pytest.raises(AttributeError):
            obj.a
        with pytest.raises(AttributeError):
            obj.b

    def test_wraps_init(self):
        """
        If *create_init* is `True`, build initializer.
        """
        obj = MagicWithInitC(a=1, b=2)
        assert 1 == obj.a
        assert 2 == obj.b

    def test_immutable(self):
        """
        If *make_immutable* is `True`, make class immutable.
        """
        @attributes(["a"], make_immutable=True)
        class ImmuClass(object):
            pass

        obj = ImmuClass(a=42)
        with pytest.raises(AttributeError):
            obj.a = "23"

    def test_optimizes(self):
        """
        Uses correct order such that with_init can us __original_setattr__.
        """
        @attributes(["a"], make_immutable=True)
        class C(object):
            __slots__ = ["a"]

        c = C(a=42)
        assert c.__original_setattr__ == c.__characteristic_setattr__

    def test_private(self):
        """
        Integration test for name mangling/aliasing.
        """
        @attributes([Attribute("_a")])
        class C(object):
            pass
        c = C(a=42)
        assert 42 == c._a

    def test_private_no_alias(self):
        """
        Integration test for name mangling/aliasing.
        """
        @attributes([Attribute("_a", keep_underscores=True)])
        class C(object):
            pass
        c = C(_a=42)
        assert 42 == c._a


class TestEnsureAttributes(object):
    def test_leaves_attribute_alone(self):
        """
        List items that are an Attribute stay an Attribute.
        """
        a = Attribute("a")
        assert a is _ensure_attributes([a])[0]

    def test_converts_rest(self):
        """
        Any other item will be transformed into an Attribute.
        """
        l = _ensure_attributes(["a"])
        assert isinstance(l[0], Attribute)
        assert "a" == l[0].name


class TestImmutable(object):
    def test_bare(self):
        """
        In an immutable class, setting an definition-time attribute raises an
        AttributeError.
        """
        @immutable(["foo"])
        class ImmuClass(object):
            foo = "bar"

        i = ImmuClass()
        with pytest.raises(AttributeError):
            i.foo = "not bar"

    def test_Attribute(self):
        """
        Mutation is caught if user passes an Attribute instance.
        """
        @immutable([Attribute("foo")])
        class ImmuClass(object):
            def __init__(self):
                self.foo = "bar"

        i = ImmuClass()
        with pytest.raises(AttributeError):
            i.foo = "not bar"

    def test_init(self):
        """
        Changes within __init__ are allowed.
        """
        @immutable(["foo"])
        class ImmuClass(object):
            def __init__(self):
                self.foo = "bar"

        i = ImmuClass()
        assert "bar" == i.foo

    def test_with_init(self):
        """
        Changes in with_init's initializer are allowed.
        """
        @immutable(["foo"])
        @with_init(["foo"])
        class ImmuClass(object):
            pass

        i = ImmuClass(foo="qux")
        assert "qux" == i.foo

    def test_Attribute_exclude_from_immutable(self):
        """
        Ignores attribute if exclude_from_immutable=True.
        """
        @immutable([Attribute("a", exclude_from_immutable=True), "b"])
        class C(object):
            def __init__(self, a, b):
                self.a = a
                self.b = b

        c = C(1, 2)
        c.a = 3
        with pytest.raises(AttributeError):
            c.b = 4


def test_nothing():
    """
    ``NOTHING`` has a sensible repr.
    """
    assert "NOTHING" == repr(NOTHING)
