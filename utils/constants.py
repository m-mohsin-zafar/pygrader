from collections import OrderedDict


class Constants:
    # Letter Grades to Score Mapping
    LETTER2SCORE = OrderedDict({
        'A': 4.00,
        'A-': 3.67,
        'B+': 3.33,
        'B': 3.00,
        'B-': 2.67,
        'C+': 2.33,
        'C': 2.00,
        'C-': 1.67,
        'D+': 1.33,
        'D': 1.00,
        'F': 0.00
    })

    def __init__(self):
        self.SCORE2LETTER = OrderedDict({v: k for k, v in self.LETTER2SCORE.items()})

    def get_grades_list(self):
        return list(self.LETTER2SCORE.keys())

    def get_grades_below(self, start_grade):
        gl = self.get_grades_list()
        start_idx = gl.index(start_grade)
        gl_below = gl[start_idx + 1:]

        return gl_below

    def get_grades_above(self, start_grade):
        gl = self.get_grades_list()
        start_idx = gl.index(start_grade)
        gl_above = gl[:start_idx]

        return gl_above


if __name__ == '__main__':
    constants = Constants()
    print(constants.LETTER2SCORE)
    print(constants.SCORE2LETTER)
    print(constants.get_grades_list())
    print(constants.get_grades_above('B'))
    print(constants.get_grades_below('B'))
