import pandas as pd
from pprint import pprint

version = None
csv_file = pd.read_csv(f'../../data/outputs/csv/{version}.csv')


# Function to generate LaTeX table from DataFrame
def generate_latex_table(df):
    latex = ''

    # Add rows
    for index, row in df.iterrows():
        for value in row[1:]:
            if value.startswith('$'):
                sign, value = value.split('$')

            elif value.endswith('%'):
                pass
            else:
                pass
        print(" & ".join(row[1:].astype(str)))
        row_latex = "\\textbf{" + row[0] + "} & " + " & ".join(row[1:].astype(str)) + " \\\\\n\n"
        latex += row_latex

    return latex


print(generate_latex_table(csv_file))
