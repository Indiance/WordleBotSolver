import re
import math
from collections import defaultdict
from multiprocessing import Pool, cpu_count

# Load all valid 5-letter lowercase words
def load_words():
    with open("words.txt", "r") as f:
        return [line.strip().lower() for line in f if len(line.strip()) == 5]

# Memoization cache for feedback
feedback_cache = {}

# Feedback parser
def get_feedback(guess, actual):
    key = (guess, actual)
    if key in feedback_cache:
        return feedback_cache[key]

    feedback = ['B'] * 5
    used_actual = [False] * 5
    used_guess = [False] * 5

    # Green pass
    for i in range(5):
        if guess[i] == actual[i]:
            feedback[i] = 'G'
            used_actual[i] = True
            used_guess[i] = True

    # Yellow pass
    for i in range(5):
        if feedback[i] == 'G':
            continue
        for j in range(5):
            if not used_actual[j] and not used_guess[i] and guess[i] == actual[j]:
                feedback[i] = 'Y'
                used_actual[j] = True
                break

    result = ''.join(feedback)
    feedback_cache[key] = result
    return result

# Filter words based on guess and feedback
def filter_words(possible_words, guess, feedback):
    def is_valid(word):
        return get_feedback(guess, word) == feedback
    return [word for word in possible_words if is_valid(word)]

# Pass both guess and possible_words to worker
def entropy_for_guess(args):
    guess, possible_words = args
    feedback_counts = defaultdict(int)
    for actual in possible_words:
        feedback = get_feedback(guess, actual)
        feedback_counts[feedback] += 1

    total = sum(feedback_counts.values())
    if total == 0:
        return (0.0, guess)

    entropy = sum(
        -(count / total) * math.log2(count / total)
        for count in feedback_counts.values()
    )

    return (entropy, guess)

# Explicitly construct list of (guess, possible_words)
def calculate_entropies_parallel(possible_words, all_words):
    args = [(guess, possible_words) for guess in all_words]
    with Pool(processes=cpu_count()) as pool:
        entropies = pool.map(entropy_for_guess, args)

    entropies.sort(reverse=True)
    return entropies

# Main driver
if __name__ == "__main__":
    all_words = load_words()
    possible_words = all_words.copy()
    first_turn = True

    while True:
        print(f"\nRemaining possible answers: {len(possible_words)}")

        guess_space = all_words if len(possible_words) > 20 else possible_words

        if not first_turn:
            print("Calculating entropy in parallel...")
            entropies = calculate_entropies_parallel(possible_words, guess_space)
            print("Top suggested guesses:")
            for i in range(min(5, len(entropies))):
                print(f"{i+1}. {entropies[i][1]} (Entropy: {entropies[i][0]:.4f})")

        # User input
        guess = input("Enter your guess (default: 'salet'): ").lower()
        if not guess:
            guess = "salet"
        first_turn = False

        if guess not in all_words:
            print("Guess not in allowed word list.")
            continue

        feedback = input("Enter feedback (G = green, Y = yellow, B = gray): ").upper()
        if len(feedback) != 5 or not re.match("^[GYB]{5}$", feedback):
            print("Invalid feedback.")
            continue

        possible_words = filter_words(possible_words, guess, feedback)

        if len(possible_words) == 1:
            print(f"\n🎉 The answer is: {possible_words[0]}")
            break
        elif len(possible_words) == 0:
            print("\n❌ No possible words remaining. Check your inputs.")
            break
