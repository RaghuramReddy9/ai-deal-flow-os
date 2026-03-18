import re

def test_money_extraction(text_lines, labels):
    """Test the improved money extraction logic."""
    for i, line in enumerate(text_lines):
        low = line.lower()

        for label in labels:
            if re.search(r'\b' + re.escape(label) + r'\b', low):
                print(f"Found label '{label}' in line: {line}")

                # Test same line
                money = re.search(r'\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K|m|M|b|B|t|T|million|billion)?\b', line)
                if money:
                    print(f"  Same line match: '{money.group(0).strip()}'")
                    return money.group(0).strip()

                # Test next lines
                for j in range(i + 1, min(i + 3, len(text_lines))):
                    candidate = text_lines[j]
                    money = re.search(r'\$?\s*[\d,]+(?:\.\d+)?\s*(?:k|K|m|M|b|B|t|T|million|billion)?\b', candidate)
                    if money:
                        print(f"  Next line match: '{money.group(0).strip()}'")
                        return money.group(0).strip()

    return None

# Test cases
test_lines = [
    "Annual Revenue $1.8 m",
    "The revenue is $3.4 million",
    "Price: $500k",
    "EBITDA $26,110",
    "60% repeat revenue",
    "Small value 1.1"
]

labels = ["revenue", "annual revenue", "profit", "ebitda"]

for line in test_lines:
    result = test_money_extraction([line], labels)
    print(f"Input: '{line}' -> Extracted: {repr(result)}")
    print()