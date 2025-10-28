"""
Test script to verify all dependencies are installed correctly.
"""

print("Testing imports...")
print("-" * 50)

try:
    import streamlit
    print(" streamlit -", streamlit.__version__)
except ImportError as e:
    print(f" streamlit: {e}")

try:
    import pandas
    print(" pandas -", pandas.__version__)
except ImportError as e:
    print(f" pandas: {e}")

try:
    import numpy
    print("numpy -", numpy.__version__)
except ImportError as e:
    print(f"numpy import error: {e}")

try:
    import matplotlib
    print("matplotlib -", matplotlib.__version__)
except ImportError as e:
    print(f"matplotlib import error: {e}")

try:
    import seaborn
    print("seaborn -", seaborn.__version__)
except ImportError as e:
    print(f"seaborn import error: {e}")

try:
    import openpyxl
    print("openpyxl -", openpyxl.__version__)
except ImportError as e:
    print(f"openpyxl import error: {e}")

print("-" * 50)
print("Import test complete!")
