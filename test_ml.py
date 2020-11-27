import pandas as pd
import numpy as np
from os.path import expanduser
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn import datasets

HOME_DIR = expanduser('~')

class Algo:

    def __init__(self):
        iris = datasets.load_iris()
        digits = datasets.load_digits()

        print type(digits)


if __name__ == "__main__":
    Algo()
