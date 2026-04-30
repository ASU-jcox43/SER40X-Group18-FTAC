import unittest
import rubric_analyzer_anthropic
import time

# This test just makes sure that this file's AI analysis is done in under two minutes. If over 120 seconds, it fails,
# otherwise it passes.

class MyTestCase(unittest.TestCase):
    def test_something(self):
        file_path = "C:/Users/Jacob/repos/SER40X/SER40X-Group18-FTAC/Backend/test_documents/Calgary_Food_Trucks_Copied_And_Pasted.txt"''
        start = time.perf_counter()
        rubric_analyzer_anthropic.download_analysis(file_path, True)
        duration = time.perf_counter() - start
        self.assertLessEqual(duration, 120)  # add assertion here


if __name__ == '__main__':
    unittest.main()
