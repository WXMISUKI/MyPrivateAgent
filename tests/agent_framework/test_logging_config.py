import json
import io
import logging
import unittest

from backend.logging_config import setup_logging, RequestIDFilter


class TestStructuredLogging(unittest.TestCase):
    def test_setup_logging_returns_logger(self):
        logger = setup_logging()
        self.assertIsInstance(logger, logging.Logger)

    def test_request_id_filter_adds_field(self):
        record = logging.LogRecord("test", logging.INFO, "", 0, "msg", (), None)
        f = RequestIDFilter()
        f.filter(record)
        self.assertTrue(hasattr(record, "request_id"))

    def test_json_output_format(self):
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        from pythonjsonlogger import jsonlogger
        handler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s"))
        handler.addFilter(RequestIDFilter())

        logger = logging.getLogger("test_json_output")
        logger.handlers = [handler]
        logger.setLevel(logging.INFO)
        logger.info("test message")

        output = stream.getvalue().strip()
        parsed = json.loads(output)
        self.assertEqual(parsed["message"], "test message")
        self.assertIn("request_id", parsed)


if __name__ == "__main__":
    unittest.main()
