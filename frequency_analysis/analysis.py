sequences: dict[str, int] = {}

SEQ_LENGTHS = (2, 3, 4)

INPUT_FILE = "valid_words"

with open(f"frequency_analysis/{INPUT_FILE}.txt", "r") as word_file:
    for line in word_file.readlines():
        word = line.strip()
        for i in range(len(word)):
            for length in SEQ_LENGTHS:
                if i + length <= len(word):
                    sequence = word[i : i + length]
                    if not sequences.get(sequence, False):
                        sequences[sequence] = 0
                    sequences[sequence] += 1

with open(f"frequency_analysis/results/{INPUT_FILE}_analysis.csv", "w") as word_file:
    for sequence in sequences:
        word_file.write(f"{sequence},{sequences[sequence]}\n")
