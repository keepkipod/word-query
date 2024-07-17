from collections import Counter
import re

def count_words(file_path):
    with open(file_path, 'r') as file:
        text = file.read().lower()
        words = re.findall(r'\b\w+\b', text)
        return Counter(words)

def process_files(file_paths):
    total_count = Counter()
    for path in file_paths:
        total_count += count_words(path)
    return total_count.most_common(10)  # Return top 10 most common words