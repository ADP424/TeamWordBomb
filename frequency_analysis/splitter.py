sequences: list[str] = []

with open(f"frequency_analysis/results/valid_words_analysis.csv", 'r') as word_file:
    for line in word_file.readlines():
        word, freq = line.strip().split(',')
        if int(freq) >= 300:
            sequences.append(word)

with open("server/resources/sequences_300.txt", 'w') as seq_file:
    for word in sequences:
        seq_file.write(f"{word}\n")
