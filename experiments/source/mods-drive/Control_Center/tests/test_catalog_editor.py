import unittest

from core.catalog_editor import CatalogEditor, CatalogEditError


class CatalogEditorTests(unittest.TestCase):
    def test_clone_recipe_does_not_mutate_donor(self):
        donor = {"recipeId": {"value": 10}, "output": [{"item": {"value": 20}}]}
        clone = CatalogEditor.clone_recipe(donor, 11, 21)
        self.assertEqual(donor["recipeId"]["value"], 10)
        self.assertEqual(clone["recipeId"]["value"], 11)
        self.assertEqual(clone["output"][0]["item"]["value"], 21)

    def test_clone_recipe_rejects_invalid_identity_or_output_shape(self):
        with self.assertRaises(CatalogEditError):
            CatalogEditor.clone_recipe({}, 0, 21)
        with self.assertRaises(CatalogEditError):
            CatalogEditor.clone_recipe({"output": {}}, 11, 21)
        with self.assertRaises(CatalogEditError):
            CatalogEditor.clone_recipe({"output": ["bad"]}, 11, 21)

    def test_clone_recipe_set_replaces_fixed_entry_in_cloned_set(self):
        bundle = {"menu": {"crafting": {"recipes": {"trees": [{"groups": [{"sets": [{"entries": [{"value": 1}, {"value": 2}]}]}]}]}}}}
        result = CatalogEditor.clone_recipe_set(bundle, 2, 99)
        sets = result.value["menu"]["crafting"]["recipes"]["trees"][0]["groups"][0]["sets"]
        self.assertEqual(len(sets), 2)
        self.assertEqual(len(sets[0]["entries"]), 2)
        self.assertEqual(sets[1]["entries"][1]["value"], 99)
        self.assertEqual(bundle["menu"]["crafting"]["recipes"]["trees"][0]["groups"][0]["sets"][0]["entries"][1]["value"], 2)

    def test_missing_donor_fails(self):
        with self.assertRaises(CatalogEditError): CatalogEditor.clone_recipe_set({"menu": {}}, 2, 3)

    def test_clone_recipe_set_rejects_duplicate_recipe_id(self):
        bundle = {"menu": {"crafting": {"recipes": {"trees": [{"groups": [{"sets": [{"entries": [{"value": 1}, {"value": 2}]}]}]}]}}}}
        with self.assertRaisesRegex(CatalogEditError, "already exists"):
            CatalogEditor.clone_recipe_set(bundle, 2, 1)

    def test_edit_recipe_is_validated_and_does_not_mutate_donor(self):
        donor = {"debugName": "old", "craftTime": 5, "output": [{"item": {"value": 20}}]}
        edited = CatalogEditor.edit_recipe(donor, {"debugName": "new", "craftTime": 7})
        self.assertEqual(donor["debugName"], "old")
        self.assertEqual(edited["debugName"], "new")
        with self.assertRaises(CatalogEditError): CatalogEditor.edit_recipe(donor, {"craftTime": -1})
        with self.assertRaises(CatalogEditError): CatalogEditor.edit_recipe(donor, {"unknown": 1})
        with self.assertRaises(CatalogEditError): CatalogEditor.edit_recipe(donor, {"ingredients": [{"item": 1, "amount": 0}]})
        with self.assertRaises(CatalogEditError): CatalogEditor.edit_recipe(donor, {"output": ["bad"]})


if __name__ == "__main__":
    unittest.main()
