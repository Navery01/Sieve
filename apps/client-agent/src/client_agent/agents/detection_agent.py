from presidio_analyzer import AnalyzerEngine
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


    def detect(self, text: str, language: str ='en', score_threshold: float = 0.5) -> list[dict]:
        """Detect PII entities in the given text using Presidio Analyzer.
        Args:
            text:  The input text to analyze for PII.
            language:  The language of the input text.
            score_threshold:  The minimum score for a detection to be considered valid.
        
        """
        results = self.analyzer.analyze(text=text, language=language, score_threshold=score_threshold)
        formatted_results = self._split_output(results)
        for result in formatted_results:
            subtext = text[result['start']:result['end']]
            result['subtext'] = subtext
        return formatted_results
    
    def huristic_detect(self, text) -> bool:
        word_bank = self._load_word_bank("word_bank.txt")
        normalized_text = text.lower()
        for word in word_bank:
            return re.search(r'\b' + re.escape(word) + r'\b', normalized_text)

    @staticmethod
    def _load_word_bank(path: str) -> list[str]:
        with open(path, "r") as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]


if __name__ == "__main__":
    agent = DetectionAgent()
    text = "My name is John Doe and my email is john.doe@example.com"
    results = agent.detect(text)

    pprint(results)
    