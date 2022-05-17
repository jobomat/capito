import unittest
import os
import json

import pymel.core as pc

from cg3.file.alembic import abc_export, abc_import
from cg3.test import TestCase


class AlembicTests(TestCase):
    CUBENAME = "MyCube"
    SPHERENAME = "MySphere"
    GROUPNAME = "MyGroup"

    def test_export_file(self):
        file = self.get_temp_filename("abc_testfile.abc")
        #file = "E:/temp_alembic.abc"

        cube = pc.polyCube(ch=False, n=self.CUBENAME)[0]
        sphere = pc.polySphere(ch=False, n=self.SPHERENAME)[0]
        group = pc.group(cube, sphere, n=self.GROUPNAME)

        abc_export(group.name(), file)
        self.assertTrue(os.path.isfile(file))

    def test_ai_attributes_get_exported_by_default(self):
        file = self.get_temp_filename("abc_testfile.abc")

        cube = pc.polyCube(ch=False, n=self.CUBENAME)[0]
        sphere = pc.polySphere(ch=False, n=self.SPHERENAME)[0]
        group = pc.group(cube, sphere, n=self.GROUPNAME)

        sphere.getShape().aiSubdivType.set(1)
        sphere.getShape().aiSubdivIterations.set(2)
        
        abc_export(group.name(), file)
        pc.delete(group)
        abc_import(file)

        sphereshape = pc.PyNode(self.SPHERENAME).getShape()
        self.assertEqual(sphereshape.aiSubdivType.get(), 1)
        self.assertEqual(sphereshape.aiSubdivIterations.get(), 2)

    def test_custom_json_string_attribute_gets_exported(self):
        file = self.get_temp_filename("abc_testfile.abc")

        json_dict = {
            "string": "BlaBlaBla",
            "int": 2,
            "list_of_ints": list(range(1000))
        }
        ATTRIBUTE_NAME = "json_data"
        cube = pc.polyCube(ch=False, n=self.CUBENAME)[0]

        cube.addAttr(ATTRIBUTE_NAME, dt="string")
        cube.setAttr(ATTRIBUTE_NAME, json.dumps(json_dict, indent=4))
        
        abc_export(cube.name(), file, attrs=["json_data"])
        pc.delete(cube)
        abc_import(file)

        cube = pc.PyNode(self.CUBENAME)
        self.assertTrue(cube.hasAttr("json_data"))
        self.assertEqual(json.loads(cube.getAttr(ATTRIBUTE_NAME)), json_dict)
        
    def test_imported_file_has_same_structure(self):
        file = self.get_temp_filename("abc_testfile.abc")

        cube = pc.polyCube(ch=False, n=self.CUBENAME)[0]
        sphere = pc.polySphere(ch=False, n=self.SPHERENAME)[0]
        group = pc.group(cube, sphere, n=self.GROUPNAME)

        abc_export(group.name(), file)

        pc.delete(group)

        abc_import(file)
        self.assertTrue(pc.objExists(self.GROUPNAME))
        group = pc.PyNode(self.GROUPNAME)
        children = [c.name() for c in group.getChildren()]
        self.assertEqual(len(children), 2)
        self.assertIn(self.CUBENAME, children)
        self.assertIn(self.SPHERENAME, children)



        
