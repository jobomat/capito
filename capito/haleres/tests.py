import unittest

from .job_utils import create_frame_list


class FrameListTestCase(unittest.TestCase):
    def test_empty_frame_text(self):
        frame_text = ""
        job_size = 5
        expected_result = []
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)
    
    def test_job_size_zero_or_negative(self):
        frame_text = "1-5"
        job_size = 0
        expected_result = []
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)
        job_size = -1
        expected_result = []
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_job_size_one(self):
        frame_text = "1-5"
        job_size = 1
        expected_result = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_single_frame(self):
        frame_text = "1"
        job_size = 5
        expected_result = [(1, 1)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_frame_range(self):
        frame_text = "1-5"
        job_size = 2
        expected_result = [(1, 2), (3, 4), (5, 5)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_multiple_ranges_and_frames(self):
        frame_text = "1-3, 5, 7-9, 11,12"
        job_size = 4
        expected_result = [(1, 3), (5, 5), (7, 9), (11, 12)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)
    
    def test_frame_text_with_strange_order(self):
        frame_text = "12, 6-10, 70-75, 1-4"
        job_size = 4
        expected_result = [(1, 4), (6, 9), (10, 10), (12, 12), (70, 73), (74, 75)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_frame_text_with_varying_seperators(self):
        frame_text = """12
        6-10; 70:75, 
        1-4"""
        job_size = 4
        expected_result = [(1, 4), (6, 9), (10, 10), (12, 12), (70, 73), (74, 75)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)

    def test_frame_text_with_duplicates(self):
        frame_text = "1, 2, 3, 2, 1"
        job_size = 5
        expected_result = [(1, 3)]
        result = create_frame_list(frame_text, job_size)
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()