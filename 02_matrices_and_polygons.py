from PySide2 import QtWidgets, QtGui, QtCore
import OpenGL.GL as gl
import OpenGL.GLU as glu
import sys


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.button = QtWidgets.QPushButton('Test', self)

        self.widget = GLWidget(self)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(self.button)
        self.setLayout(self.mainLayout)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Q:
            self.widget.toggleColorMode()
        elif event.key() == QtCore.Qt.Key_E:
            self.widget.toggleProjectionScale()
        super().keyPressEvent(event)


class GLWidget(QtWidgets.QOpenGLWidget):

    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480
    SCREEN_FPS = 60

    COLOR_MODE_CYAN = 0
    COLOR_MODE_MULTI = 1

    color_mode = COLOR_MODE_CYAN
    projection_scale = 2
    MAX_COUNT = 5

    def __init__(self, parent):
        super().__init__(parent)
        self.start_timer()

    def start_timer(self):
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000/self.SCREEN_FPS)

    def minimumSizeHint(self):
        return QtCore.QSize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    def sizeHint(self):
        return QtCore.QSize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

    def getOpenglInfo(self):
        info = """
            Vendor: {0}
            Renderer: {1}
            OpenGL Version: {2}
            Shader Version: {3}
        """.format(
            gl.glGetString(gl.GL_VENDOR),
            gl.glGetString(gl.GL_RENDERER),
            gl.glGetString(gl.GL_VERSION),
            gl.glGetString(gl.GL_SHADING_LANGUAGE_VERSION)
        )
        return info

    def initializeGL(self) -> bool:
        print(self.getOpenglInfo())

        gl.glClearColor(0.3, 0.1, 0.3, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        # gl.glShadeModel(gl.GL_FLAT)
        # gl.glEnable(gl.GL_DEPTH_TEST)
        # gl.glEnable(gl.GL_CULL_FACE)

        error = gl.glGetError()
        if not error == gl.GL_NO_ERROR:
            print("Error Initializing OpenGL! %s" % glu.gluErrorString(error),
                  file=sys.stderr)
            return False

        return True

    def resizeGL(self, width, height) -> bool:

        self.SCREEN_WIDTH = width
        self.SCREEN_HEIGHT = height

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        gl.glOrtho(-width/2 * self.projection_scale,
                   width/2 * self.projection_scale,
                   -height/2 * self.projection_scale,
                   height/2 * self.projection_scale,
                   -1, 1)

        error = gl.glGetError()
        if not error == gl.GL_NO_ERROR:
            print("Error Initializing OpenGL! %s" % gl.gluErrorString(error),
                  file=sys.stderr)
            return False

        return True

    def paintGL(self):

        self.resizeGL(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glColor3f(1.0, 1.5, 0.0)

        if self.color_mode == self.COLOR_MODE_CYAN:
            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(0, 1, 1)
            gl.glVertex2f(-50, -50)
            gl.glVertex2f(50, -50)
            gl.glVertex2f(50,  50)
            gl.glVertex2f(-50,  50)
            gl.glEnd()
        else:
            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(1, 0, 0)
            gl.glVertex2f(-50, -50)
            gl.glColor3f(1, 1, 0)
            gl.glVertex2f(50, -50)
            gl.glColor3f(0, 1, 0)
            gl.glVertex2f(50,  50)
            gl.glColor3f(0, 0, 1)
            gl.glVertex2f(-50,  50)
            gl.glEnd()

        gl.glFlush()

    def toggleColorMode(self):
        self.color_mode = int(not self.color_mode)

    def toggleProjectionScale(self):
        if self.projection_scale == 1:
            self.projection_scale = 2
        elif self.projection_scale == 2:
            self.projection_scale = 0.5
        elif self.projection_scale == 0.5:
            self.projection_scale = 1


if __name__ == "__main__":
    app = QtWidgets.QApplication(['Hey Hey'])
    window = MainWindow()
    window.show()
    app.exec_()
