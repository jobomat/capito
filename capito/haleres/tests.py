import unittest

from .utils import create_frame_tuple_list


class FrameListTestCase(unittest.TestCase):
    def test_empty_frame_text(self):
        frame_text = ""
        job_size = 5
        expected_result = []
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)
    
    def test_job_size_zero_or_negative(self):
        frame_text = "1-5"
        job_size = 0
        expected_result = []
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)
        job_size = -1
        expected_result = []
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_job_size_one(self):
        frame_text = "1-5"
        job_size = 1
        expected_result = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_single_frame(self):
        frame_text = "1"
        job_size = 5
        expected_result = [(1, 1)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_frame_range(self):
        frame_text = "1-5"
        job_size = 2
        expected_result = [(1, 2), (3, 4), (5, 5)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_multiple_ranges_and_frames(self):
        frame_text = "1-3, 5, 7-9, 11,12"
        job_size = 4
        expected_result = [(1, 3), (5, 5), (7, 9), (11, 12)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)
    
    def test_frame_text_with_strange_order(self):
        frame_text = "12, 6-10, 70-75, 1-4"
        job_size = 4
        expected_result = [(1, 4), (6, 9), (10, 10), (12, 12), (70, 73), (74, 75)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_frame_text_with_varying_seperators(self):
        frame_text = """12
        6-10; 70:75, 
        1-4"""
        job_size = 4
        expected_result = [(1, 4), (6, 9), (10, 10), (12, 12), (70, 73), (74, 75)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_frame_text_with_duplicates(self):
        frame_text = "1, 2, 3, 2, 1"
        job_size = 5
        expected_result = [(1, 3)]
        result = create_frame_tuple_list(frame_text, job_size)
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()



# import sys

# capito_path = "/mnt/cg/pipeline/capito"
# settings = "/mnt/cg/pipeline/hlrs/settings.json"

# sys.path.append(capito_path)
# from capito.haleres.settings import Settings
# from capito.haleres.job import JobProvider
# from capito.haleres.hlrs import HLRS

# haleres_settings = Settings(settings)
# jp = JobProvider(haleres_settings)
# hlrs = HLRS(settings)

# hlrs_server = f"{haleres_settings.hlrs_user}@{haleres_settings.hlrs_server}"


# ###########################################

# from pathlib import Path
# import sys
# import subprocess
# from datetime import datetime
# import time

# # First get the parameters:
# capito_path = "/mnt/cg/pipeline/capito"
# haleres_settings_file = "/mnt/cg/pipeline/hlrs/settings.json"

# # Make capito availible for import:
# sys.path.append(capito_path)
# from capito.haleres.settings import Settings
# from capito.haleres.job import JobProvider
# from capito.haleres.hlrs import HLRS

# haleres_settings = Settings(haleres_settings_file)
# jp = JobProvider(haleres_settings)
# hlrs = HLRS(haleres_settings_file)

# # Get local data
# jobs_to_delete = jp.get_jobs_to_delete()
# print(f"{jobs_to_delete:}")
# jobs_to_push = jp.get_jobs_to_push()
# print(f"{jobs_to_push:}")
# unfinished_jobs = jp.get_unfinished_jobs()
# print(f"{unfinished_jobs:}")