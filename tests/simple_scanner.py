import unittest

import os
from os.path import join

import time

from tests.util import with_file_structure

# noinspection PyProtectedMember
from fspy.agent.scanner import SimpleComparator, _file_state_from_file_path, FileDiff


class SimpleScanner(unittest.TestCase):

    @with_file_structure({"a.txt": 10, "b.txt": 20})
    def test_no_changes(self, wd):
        c = SimpleComparator(wd)
        first_diff = c.scan()

        self.assertIsNone(first_diff)

        second_diff = c.scan()

        self.assertFalse(second_diff)

    @with_file_structure({"a.txt": 10, "b.txt": 20, "dir1": {"c.txt": 30}})
    def test_delete(self, wd):
        c = SimpleComparator(wd)

        file_to_delete = join(wd, "dir1", "c.txt")

        expected_deleted_file_state = _file_state_from_file_path(file_to_delete)

        c.scan()

        os.remove(file_to_delete)

        f_diff = c.scan()

        self.assertEqual([expected_deleted_file_state], f_diff.deleted)
        self.assertEqual([], f_diff.updated)
        self.assertEqual([], f_diff.created)

        self.assertTrue(f_diff)

    @with_file_structure({"a.txt": 10, "b.txt": 20})
    def test_update_same_size(self, wd):
        c = SimpleComparator(wd)

        file_to_update = join(wd, "a.txt")

        c.scan()

        expected_updated_file_state_before = _file_state_from_file_path(file_to_update)

        # Resolution for mtime/ctime is 1 second for some platforms
        time.sleep(1)

        with open(file_to_update, "wb") as fd:
            fd.write(b"\0" * 10)

        expected_updated_file_state_after = _file_state_from_file_path(file_to_update)

        f_diff = c.scan()

        self.assertEqual([], f_diff.deleted)
        self.assertEqual(
            [FileDiff(
                before=expected_updated_file_state_before,
                after=expected_updated_file_state_after,
            )],
            f_diff.updated
        )
        self.assertEqual([], f_diff.created)

        self.assertTrue(f_diff)

    @with_file_structure({"a.txt": 10, "b.txt": 20})
    def test_create(self, wd):
        c = SimpleComparator(wd)

        file_to_create = join(wd, "c.txt")

        c.scan()

        with open(file_to_create, "wb") as fd:
            fd.write(b"a" * 30)

        expected_created_file_state = _file_state_from_file_path(file_to_create)

        f_diff = c.scan()

        self.assertEqual([], f_diff.deleted)
        self.assertEqual([], f_diff.updated)
        self.assertEqual([expected_created_file_state], f_diff.created)

        self.assertTrue(f_diff)


if __name__ == '__main__':
    unittest.main()
