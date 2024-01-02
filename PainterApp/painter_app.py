import cv2
import numpy as np
import math
from enum import Enum


class Modes(Enum):
    CIRCLE = 1
    RECTANGLE = 2
    POLYGON = 3
    ERASER = 4
    CROP = 5


class Constants:
    CIRCLE_KEY = ord('c')
    RECTANGLE_KEY = ord('r')
    POLYGON_KEY = ord('p')
    # Exit key is the 'ESC' key
    EXIT_KEY = 27
    DRAW_POLYGON_KEY = ord('d')
    UNDO_KEY = ord('u')
    REDO_KEY = ord('y')
    ROTATE_RIGHT_KEY = ord('l')
    ROTATE_LEFT_KEY = ord('k')
    ERASER_KEY = ord('e')
    ERASER_SIZE = 25  # The size of the eraser is constant
    CROP_KEY = ord('x')
    ANGLE_LEFT = 90
    ANGLE_RIGHT = -90


class Painter:
    # Initialize the class variables and constants
    def __init__(self):
        self.board_size = [0, 0]
        self.board_color = [255, 255, 255]
        self.drawing_color = [0, 0, 0]
        self.preview_color = [0, 0, 0]
        self.board = None

        self.current_mode = Modes.CIRCLE  # set the circle mode as the defualt mode.
        self.polygon_points = []
        self.rotation_mode = 0

        self.crop_points = []

        self.boards_stack = []
        self.redo_stack = []

        self.start_x, self.start_y = -1, -1
        self.cursor_x, self.cursor_y = -1, -1
        self.is_drawing = False
        self.is_erasing = False

    # A function that returns the inverse color of the given color (Used to change the drawing color depending on the background color).
    def get_inverse_color(self, color):
        return [255 - color[0], 255 - color[1], 255 - color[2]]

    def set_brighness(self, brightness):  # Used to set the brightness of the preview color.
        if self.drawing_color[0] >= 0 and self.drawing_color[1] >= 0 and self.drawing_color[2] >= 0 and \
                self.drawing_color[0] <= 50 and self.drawing_color[1] <= 50 and self.drawing_color[2] <= 50:
            color = 255 * brightness
            return [color, color, color]
        return [self.drawing_color[0] * brightness, self.drawing_color[1] * brightness,
                self.drawing_color[2] * brightness]

    # A function that calculate the distance between 2 points (used for drawing circles).
    def calculate_distance(self, x1, y1):
        return int(math.sqrt((x1 - self.start_x) ** 2 + (y1 - self.start_y) ** 2))

    def draw_circle(self, x, y, board=None, is_preview=False):
        if board is None:
            board = self.board
        radius = self.calculate_distance(x, y)
        if is_preview:
            cv2.circle(board, (self.start_x, self.start_y), radius, self.preview_color, 2)
        else:
            cv2.circle(board, (self.start_x, self.start_y), radius, self.drawing_color, 2)
            if len(self.redo_stack) > 0:
                self.redo_stack.clear()
            self.boards_stack.append(self.board.copy())

    def draw_polygon(self, is_preview=False, board=None):
        if board is None:
            board = self.board
        if is_preview:
            cv2.polylines(board, np.array([self.polygon_points]), True, self.preview_color, 2)
        else:
            cv2.polylines(board, np.array([self.polygon_points]), True, self.drawing_color, 2)
            self.polygon_points.clear()
            if len(self.redo_stack) > 0:
                self.redo_stack.clear()
            self.boards_stack.append(self.board.copy())

    def draw_rectangle(self, x, y, board=None, is_preview=False):
        if board is None:
            board = self.board
        if is_preview:
            cv2.rectangle(board, (self.start_x, self.start_y), (x, y), self.preview_color, 2)
        else:
            cv2.rectangle(board, (self.start_x, self.start_y), (x, y), self.drawing_color, 2)
            if len(self.redo_stack) > 0:
                self.redo_stack.clear()
            self.boards_stack.append(self.board.copy())

    def display_placeholder(self, board=None):
        if board is None:
            board = self.board
        if self.current_mode == Modes.CIRCLE and self.start_x != -1 and self.start_y != -1:
            self.draw_circle(self.cursor_x, self.cursor_y, board, True)
        elif self.current_mode == Modes.RECTANGLE and self.start_x != -1 and self.start_y != -1:
            self.draw_rectangle(self.cursor_x, self.cursor_y, board, True)
        elif self.current_mode == Modes.POLYGON:
            cv2.putText(board, "Press 'd' to draw the polygon", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        self.drawing_color, 2)
            self.draw_polygon(True, board)
        elif self.current_mode == Modes.ERASER:
            cv2.rectangle(board, (self.cursor_x - Constants.ERASER_SIZE, self.cursor_y - Constants.ERASER_SIZE),
                            (self.cursor_x + Constants.ERASER_SIZE, self.cursor_y + Constants.ERASER_SIZE),
                            self.drawing_color, 1)

    def erase_region(self, x, y):
        cv2.rectangle(self.board, (x - Constants.ERASER_SIZE, y - Constants.ERASER_SIZE),
                        (x + Constants.ERASER_SIZE, y + Constants.ERASER_SIZE), self.board_color, -1)
        if len(self.redo_stack) > 0:
            self.redo_stack.clear()
        self.boards_stack.append(self.board.copy())

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.current_mode == Modes.POLYGON:
                self.polygon_points.append([x, y])
            elif self.current_mode == Modes.ERASER:
                self.is_erasing = True
            elif self.current_mode == Modes.CROP:
                self.crop_points.append([x, y])
            else:  # CIRCLE MODE OR RECTANGLE MODE
                self.start_x = x
                self.start_y = y
            self.is_drawing = True

        if event == cv2.EVENT_MOUSEMOVE:
            self.cursor_x = x
            self.cursor_y = y
            if self.is_erasing:
                self.erase_region(x, y)

        if event == cv2.EVENT_LBUTTONUP and self.current_mode != Modes.POLYGON:
            if self.current_mode == Modes.CIRCLE:
                # print("Drawing circle")
                self.draw_circle(x, y)
            elif self.current_mode == Modes.RECTANGLE:  # RECTANGLE MODE
                self.draw_rectangle(x, y)

            self.is_erasing, self.is_drawing = False, False

    def run(self):
        self.board_size[0] = int(input("Enter board width: "))
        self.board_size[1] = int(input("Enter board height: "))

        self.board_color[0] = int(input("Enter board 'BLUE' value (0-255): "))
        self.board_color[1] = int(input("Enter board 'GREEN' value (0-255): "))
        self.board_color[2] = int(input("Enter board 'RED' value (0-255): "))

        # Make sure that the range of colors are between 0 - 255 (inclusive)
        self.board_color[0] = max(0, min(self.board_color[0], 255))
        self.board_color[1] = max(0, min(self.board_color[1], 255))
        self.board_color[2] = max(0, min(self.board_color[2], 255))

        self.drawing_color = self.get_inverse_color(self.board_color)
        self.preview_color = self.set_brighness(0.6)

        # Show another window that displays controls for the user
        cv2.namedWindow("Controls")
        text_color = [255, 255, 255]

        controls_window_image = np.zeros((400, 500, 3), np.uint8)
        cv2.putText(controls_window_image, "Controls", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'c' to switch to CIRCLE mode", (10, 60), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'r' to switch to RECTANGLE mode", (10, 90), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'p' to switch to POLYGON mode", (10, 120), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'e' to switch to ERASER mode", (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'x' to switch to CROP mode", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    text_color, 2)
        cv2.putText(controls_window_image, "Press 'd' to draw the polygon", (10, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    text_color, 2)
        cv2.putText(controls_window_image, "Press 'u' to undo", (10, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'y' to redo", (10, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color, 2)
        cv2.putText(controls_window_image, "Press 'l' to rotate right", (10, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    text_color, 2)
        cv2.putText(controls_window_image, "Press 'k' to rotate left", (10, 330), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    text_color, 2)
        cv2.putText(controls_window_image, "Press 'ESC' to exit", (10, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, text_color,
                    2)

        cv2.imshow("Controls", controls_window_image)
        cv2.moveWindow("Controls", 0, 0)

        self.board = np.full((self.board_size[0], self.board_size[1], 3), self.board_color, dtype=np.uint8)

        cv2.namedWindow("Main Window")
        cv2.setMouseCallback("Main Window", self.mouse_callback)

        center = (self.board_size[0] // 2, self.board_size[1] // 2)
        key = cv2.waitKey(1)

        self.boards_stack.append(self.board.copy())

        while key != Constants.EXIT_KEY:
            current_board = self.board.copy()
            cv2.putText(current_board, "Current Mode: " + str(self.current_mode.name), (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.drawing_color, 2)

            if self.rotation_mode != 0:
                self.board = cv2.warpAffine(self.board, cv2.getRotationMatrix2D(center, self.rotation_mode, 1.0),
                                            (self.board_size[0], self.board_size[1]))
                self.rotation_mode = 0

            # display a placeholder for the current object that the user is drawing
            if self.is_drawing:
                self.display_placeholder(current_board)

            # To prevent the text to rotate with the image
            cv2.putText(current_board, "Press 'ESC' to exit", (self.board_size[0] - 230, 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, self.drawing_color, 2)

            cv2.imshow("Main Window", current_board)
            key = cv2.waitKey(1)

            if key == Constants.CIRCLE_KEY:
                if self.current_mode == Modes.POLYGON:  # clear the polygon points if the user was drawing a polygon
                    self.polygon_points.clear()

                self.current_mode = Modes.CIRCLE

            elif key == Constants.RECTANGLE_KEY:
                self.current_mode = Modes.RECTANGLE

            elif key == Constants.POLYGON_KEY:
                if self.current_mode == Modes.POLYGON:
                    self.polygon_points.clear()

                self.current_mode = Modes.POLYGON

            elif key == Constants.ERASER_KEY:
                if self.current_mode == Modes.POLYGON:
                    self.polygon_points.clear()

                self.current_mode = Modes.ERASER

            elif key == Constants.CROP_KEY:
                if self.current_mode == Modes.POLYGON:
                    self.polygon_points.clear()

                self.current_mode = Modes.CROP

            elif key == Constants.UNDO_KEY:
                if len(self.boards_stack) > 0:
                    board = self.boards_stack.pop()
                    self.redo_stack.append(board)
                    self.board = board.copy()

            elif key == Constants.REDO_KEY:
                if len(self.redo_stack) > 0:
                    self.boards_stack.append(self.board.copy())
                    self.board = self.redo_stack.pop()

            elif key == Constants.DRAW_POLYGON_KEY and self.current_mode == Modes.POLYGON:
                self.draw_polygon(False)

            elif key == Constants.ROTATE_LEFT_KEY:
                self.rotation_mode = Constants.ANGLE_LEFT

            elif key == Constants.ROTATE_RIGHT_KEY:
                self.rotation_mode = Constants.ANGLE_RIGHT

        cv2.destroyAllWindows()
        return


def main():
    painter = Painter()
    painter.run()
    return


if __name__ == "__main__":
    main()
