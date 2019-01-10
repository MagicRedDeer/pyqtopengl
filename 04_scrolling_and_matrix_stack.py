from PySide2 import QtWidgets, QtGui, QtCore
import OpenGL.GL as gl
import OpenGL.GLU as glu


class MainWindow(QtWidgets.QWidget):

    speed = 16

    def __init__(self):
        super(MainWindow, self).__init__()
        self.widget = GLWidget(self)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.widget)
        self.setLayout(self.mainLayout)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_W:
            self.widget.moveCameraY(-self.speed)
        elif event.key() == QtCore.Qt.Key_S:
            self.widget.moveCameraY(self.speed)
        elif event.key() == QtCore.Qt.Key_A:
            self.widget.moveCameraX(-self.speed)
        elif event.key() == QtCore.Qt.Key_D:
            self.widget.moveCameraX(self.speed)
        super().keyPressEvent(event)


class GLWidget(QtWidgets.QOpenGLWidget):

    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480
    SCREEN_FPS = 60

    camera_x = 0
    camera_y = 0

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

    def initializeGL(self):
        print(self.getOpenglInfo())

        # initialize the projection matrix
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0.0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, -1, 1)

        # initialize the modelview matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # Save the modelview matrix
        gl.glPushMatrix()

        # Initialize clear color
        gl.glClearColor(0, 0, 0, 1)

        error = gl.glGetError()
        if not error == gl.GL_NO_ERROR:
            print("Error Iniitalizing OpenGL! %s" % glu.gluErrorString(error))
            return False

        return True

    def setCamera(self):
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()

        # move the camera
        gl.glTranslatef(-self.camera_x, -self.camera_y, 0)
        self.camera_x, self.camera_y = 0, 0

        # save default matrix with camera translation
        gl.glPushMatrix()

    def quad_vertices(self):
        gl.glVertex2f(-self.SCREEN_WIDTH//4, -self.SCREEN_HEIGHT//4)
        gl.glVertex2f(self.SCREEN_WIDTH//4, -self.SCREEN_HEIGHT//4)
        gl.glVertex2f(self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4)
        gl.glVertex2f(-self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4)

    def paintGL(self):
        gl.glViewport(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        self.setCamera()

        # clear color buffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        # Pop default matrix onto current matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)

        # red quad
        gl.glTranslatef(self.SCREEN_WIDTH/2, self.SCREEN_HEIGHT/2, 0)
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(1, 0, 0)
        self.quad_vertices()
        gl.glEnd()

        # green quad
        gl.glTranslatef(self.SCREEN_WIDTH, 0, 0)
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(0, 1, 0)
        self.quad_vertices()
        gl.glEnd()

        # blue quad
        gl.glTranslatef(0, self.SCREEN_HEIGHT, 0)
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(0, 0, 1)
        self.quad_vertices()
        gl.glEnd()

        # yellow quad
        gl.glTranslatef(-self.SCREEN_WIDTH, 0, 0)
        gl.glBegin(gl.GL_QUADS)
        gl.glColor3f(1, 1, 0)
        self.quad_vertices()
        gl.glEnd()

        gl.glFlush()

    def moveCameraX(self, value):
        self.camera_x += value

    def moveCameraY(self, value):
        self.camera_y += value


if __name__ == "__main__":
    app = QtWidgets.QApplication(['Hey Hey'])
    window = MainWindow()
    window.show()
    app.exec_()
