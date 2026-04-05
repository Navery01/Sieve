from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from pprint import pprint
import re

class DetectionAgent:
    def __init__(self):
        self.analyzer = AnalyzerEngine()

    def _split_output(self, results):
        split_results = []
        for result in results:
            split_result = {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score
            }
            split_results.append(split_result)
        return split_results
    
    def _get_subtext(self, text, start, end):
        return text[start:end]

    def detect(self, text, language='en', score_threshold=0.5):
        results = self.analyzer.analyze(text=text, language=language, score_threshold=score_threshold)
        formatted_results = self._split_output(results)
        for result in formatted_results:
            subtext = self._get_subtext(text, result['start'], result['end'])
            result['subtext'] = subtext
        return formatted_results
    
    def huristic_detect(self, text):
        word_bank = [] #TODO: populate with common PII columns/document names
        normalized_text = text.lower()
        for word in word_bank:
            if re.search(r'\b' + re.escape(word) + r'\b', normalized_text):
                print(f"Found potential PII: {word}")



if __name__ == "__main__":
    agent = DetectionAgent()
    text = "My name is John Doe and my email is john.doe@example.com"
    results = agent.detect(text)

    pprint(results)
    