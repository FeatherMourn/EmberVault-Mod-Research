"""Tests for type-name conversion and type expression parsing."""

from __future__ import annotations

import unittest

from architect_lua_config_lab.core.type_parser import (
    lua_class_to_resource_type,
    parse_type_expression,
    resource_type_to_lua_class,
)


class TypeNameConversionTests(unittest.TestCase):
    def test_simple_conversion(self):
        self.assertEqual(
            lua_class_to_resource_type("keen.BalancingTable"),
            "keen::BalancingTable",
        )

    def test_nested_namespace_conversion(self):
        self.assertEqual(
            lua_class_to_resource_type("keen.ecs.TemplateResource"),
            "keen::ecs::TemplateResource",
        )

    def test_round_trip(self):
        for name in ("keen.BalancingTable", "keen.ecs.GameSettings",
                     "keen.anim_graph.runtime_graph.AnimationGraphResource2_0"):
            self.assertEqual(
                resource_type_to_lua_class(lua_class_to_resource_type(name)),
                name,
            )

    def test_idempotent_for_already_qualified(self):
        self.assertEqual(
            lua_class_to_resource_type("keen::BalancingTable"),
            "keen::BalancingTable",
        )


class TypeExpressionTests(unittest.TestCase):
    def test_primitives(self):
        for kind in ("bool", "u8", "u16", "u32", "u64",
                     "i8", "i16", "i32", "i64",
                     "f16", "f32", "f64", "string"):
            expr = parse_type_expression(kind)
            self.assertEqual(expr.kind, kind, kind)

    def test_guid(self):
        expr = parse_type_expression("Guid")
        self.assertEqual(expr.kind, "guid")

    def test_object_reference(self):
        expr = parse_type_expression("ObjectReference<keen.LocaTag>")
        self.assertEqual(expr.kind, "reference")
        self.assertEqual(expr.name, "keen.LocaTag")

    def test_array(self):
        expr = parse_type_expression("Array<keen.Achievement>")
        self.assertEqual(expr.kind, "array")
        self.assertEqual(expr.inner.kind, "named")
        self.assertEqual(expr.inner.name, "keen.Achievement")

    def test_static_array(self):
        expr = parse_type_expression("StaticArray<f32, 4>")
        self.assertEqual(expr.kind, "static_array")
        self.assertEqual(expr.size, 4)
        self.assertEqual(expr.inner.kind, "f32")

    def test_bitmask(self):
        expr = parse_type_expression("Bitmask<keen.AmbientTags>")
        self.assertEqual(expr.kind, "bitmask")
        self.assertEqual(expr.name, "keen.AmbientTags")

    def test_variant(self):
        expr = parse_type_expression("Variant<T>")
        self.assertEqual(expr.kind, "variant")

    def test_optional(self):
        expr = parse_type_expression("u32?")
        self.assertEqual(expr.kind, "u32")
        self.assertTrue(expr.nullable)

    def test_nested_generic(self):
        expr = parse_type_expression("Array<ObjectReference<keen.SoundContainer>>")
        self.assertEqual(expr.kind, "array")
        self.assertEqual(expr.inner.kind, "reference")
        self.assertEqual(expr.inner.name, "keen.SoundContainer")

    def test_named_class(self):
        expr = parse_type_expression("keen.SomeNestedType")
        self.assertEqual(expr.kind, "named")
        self.assertEqual(expr.name, "keen.SomeNestedType")


if __name__ == "__main__":
    unittest.main()
