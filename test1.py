import os
from collections import Counter
import matplotlib.pyplot as plt

from keystroke import getKeyPresses

filepath = os.path.join(
        os.path.expanduser('~'), 
        'keystrokes.log'
    )

file = open(filepath, 'r')
contents = file.read()

freq = Counter(getKeyPresses(contents))
plt.bar(freq.keys(), freq.values())
plt.xticks(rotation=90)
plt.show()