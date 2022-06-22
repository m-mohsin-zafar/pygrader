import pandas as pd
from utils.constants import Constants
from math import floor
from pandas import DataFrame
from copy import deepcopy
from collections import OrderedDict


class Utilities:

    def __init__(self):
        self._cons = Constants()

    def load_data(self, fp=None):
        df = None
        if fp is None:
            df = pd.read_csv('../data/sample.csv')
        else:
            df = pd.read_csv(fp)

        return df

    def create_grade_intervals(self, data_df, start_grade='B', floor_avg=True):
        data_df['Marks'] = pd.to_numeric(data_df['Marks'])
        avg = data_df['Marks'].mean() if not floor_avg else floor(data_df['Marks'].mean())
        std_dev = data_df['Marks'].std()

        grades_above = self._cons.get_grades_above(start_grade)
        grades_below = self._cons.get_grades_below(start_grade)

        grades, lower_bounds, upper_bounds = [], [], []

        grades.append(start_grade)
        lower_bounds.append(avg)
        upper_bounds.append(avg + std_dev/2)

        for g in grades_above[::-1]:
            grades.insert(0, g)
            lower_bounds.insert(0, upper_bounds[0])
            upper_bounds.insert(0, lower_bounds[0] + std_dev/2)

        for g in grades_below:
            grades.append(g)
            lower_bounds.append(lower_bounds[-1] - std_dev/2)
            upper_bounds.append(lower_bounds[-1] + std_dev/2)

        # for g, l, u in zip(grades, lower_bounds, upper_bounds):
        #     print('{}\t\t{}\t\t{}'.format(g, l, u))

        grade_intervals = {
            'Grade': grades,
            'Lower Bound': lower_bounds,
            'Upper Bound': upper_bounds
        }

        return grade_intervals

    def assign_grades(self, intervals_df: DataFrame, data_df: DataFrame):
        letter_grades = []
        grade_points = []

        # 1. Loop through data_df row by row
        for ix, row in data_df.iterrows():
            # 2. Compute Letter Grades
            lg, gp = self.compute_grades_n_points(intervals_df, row['Marks'])

            letter_grades.append(lg)
            grade_points.append(gp)

        _df = deepcopy(data_df)
        _df['Letter Grades'] = letter_grades
        _df['Grade Points'] = grade_points

        return _df

    def compute_grades_n_points(self, idf, marks):
        if marks >= float(idf.iloc[0]['Lower Bound']):
            return idf.iloc[0]['Grade'], self._cons.LETTER2SCORE[idf.iloc[0]['Grade']]
        elif marks < float(idf.iloc[-1]['Upper Bound']):
            return idf.iloc[-1]['Grade'], self._cons.LETTER2SCORE[idf.iloc[-1]['Grade']]
        else:
            for ix, irow in idf.iterrows():
                if irow['Grade'] != 'A' and irow['Grade'] != 'F':
                    if (marks >= float(irow['Lower Bound'])) and (marks <= float(irow['Upper Bound'])):
                        return irow['Grade'], self._cons.LETTER2SCORE[irow['Grade']]

    def compute_grade_dist_table(self, data_df):
        mean_gpa = data_df['Grade Points'].mean()
        _grade_counts = data_df['Letter Grades'].value_counts()

        ordered_counts = []
        for k in self._cons.LETTER2SCORE.keys():
            if k in _grade_counts.keys():
                ordered_counts.append(_grade_counts[k])
            else:
                ordered_counts.append(0)

        _grade_dist_table = OrderedDict(
            {
                'Letter Grades': list(self._cons.LETTER2SCORE.keys()),
                'Grade Points': list(self._cons.LETTER2SCORE.values()),
                'Count': ordered_counts
             }
        )

        return mean_gpa, _grade_dist_table


if __name__ == '__main__':
    utils =  Utilities()
    df = utils.load_data()
    idf = DataFrame(utils.create_grade_intervals(df, 'B'))
    ndf = utils.assign_grades(idf, df)
    mean, gdt = utils.compute_grade_dist_table(ndf)
    gdt_df = DataFrame(gdt)