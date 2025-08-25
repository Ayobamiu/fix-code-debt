# generate a sample code for a simple python function that takes a string and returns the number of vowels in the string

def count_vowels(str):
    vowels = "aeiouAEIOU"
    count = 0
    for char in str:
        if char in vowels:
            count += 1
    return count