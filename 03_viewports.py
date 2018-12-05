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
            self.widget.toggleViewportMode()
        super().keyPressEvent(event)


class GLWidget(QtWidgets.QOpenGLWidget):

    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480
    SCREEN_FPS = 60

    class VPModes:
        VIEWPORT_MODE_FULL = 1
        VIEWPORT_MODE_HALF_CENTER = 2
        VIEWPORT_MODE_HALF_TOP = 3
        VIEWPORT_MODE_QUAD = 4
        VIEWPORT_MODE_RADAR = 5

    viewport_mode = VPModes.VIEWPORT_MODE_FULL

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

        gl.glOrtho(-self.SCREEN_WIDTH,
                   self.SCREEN_WIDTH,
                   self.SCREEN_HEIGHT,
                   -self.SCREEN_HEIGHT,
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

        if self.viewport_mode == self.VPModes.VIEWPORT_MODE_FULL:
            gl.glViewport(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(1, 0, 0)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

        elif self.viewport_mode == self.VPModes.VIEWPORT_MODE_HALF_CENTER:
            gl.glViewport(self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4,
                          self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(0, 1, 0)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

        elif self.viewport_mode == self.VPModes.VIEWPORT_MODE_HALF_TOP:
            gl.glViewport(self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//2,
                          self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(0, 0, 1)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

        elif self.viewport_mode == self.VPModes.VIEWPORT_MODE_QUAD:
            gl.glViewport(0, 0, self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(1, 0, 0)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

            gl.glViewport(self.SCREEN_WIDTH//2, 0,
                          self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(0, 1, 0)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

            gl.glViewport(0, self.SCREEN_HEIGHT//2,
                          self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(0, 0, 1)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

            gl.glViewport(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2,
                          self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(1, 1, 0)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

        if self.viewport_mode == self.VPModes.VIEWPORT_MODE_RADAR:
            gl.glViewport(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(1, 1, 1)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

            gl.glViewport(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2,
                          self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT//2)

            gl.glBegin(gl.GL_QUADS)
            gl.glColor3f(0.1, 0.1, 0.1)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, -self.SCREEN_HEIGHT/2)
            gl.glVertex2f(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glVertex2f(-self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2)
            gl.glEnd()

        gl.glFlush()

    def toggleViewportMode(self):
        self.viewport_mode += 1
        if self.viewport_mode > self.VPModes.VIEWPORT_MODE_RADAR:
            self.viewport_mode = 0


if __name__ == "__main__":
    app = QtWidgets.QApplication(['Hey Hey'])
    window = MainWindow()
    window.show()
    app.exec_()
