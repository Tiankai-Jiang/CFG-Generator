import ast
def spiralOrder(self, matrix):
    """
    :type matrix: List[List[int]]
    :rtype: List[int]
    """
    right = True
    down = False
    left = False
    up = False
    answer = []

    while matrix:
        print(matrix)
        if right:
            answer += matrix[0]
            del matrix[0]
            right = False
            down = True
        elif down:
            for i in range(0, len(matrix)):
                answer += [matrix[i][-1]]
                del matrix[i][-1]
            if len(matrix[0]) == 0:
                matrix = []
            down = False
            left = True
        elif left:
            temp = matrix[-1]
            temp = temp[::-1]
            answer += temp
            del matrix[-1]
            left = False
            up = True
        elif up:
            for i in range(len(matrix) - 1, -1, -1):
                answer += [matrix[i][0]]
                del matrix[i][0]
            if len(matrix[0]) == 0:
                matrix = []
            up = False
            right = True
    return answer