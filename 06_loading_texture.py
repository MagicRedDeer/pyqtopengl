from PySide2 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import sys
import os


class Texture(object):

    def __init__(self):
        self.tid = 0
        self.width = 0
        self.height = 0

    def loadTextureFromImage(self, image: np.array):
        self.height = image.shape[0]
        self.width = image.shape[1]

        assert(image.shape[2] == 3)
        assert(image.dtype == np.dtype('uint8'))

        self.tid = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, self.tid)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.width,
                        self.height, 0, gl.GL_BGR, gl.GL_UNSIGNED_BYTE, image)

        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        error = gl.glGetError()
        if error != gl.GL_NO_ERROR:
            print('Error loading pixels from image! %s' %
                  glu.gluErrorString(error), file=sys.stderr)
            return False

        return True

    def loadTextureFromFile(self, path):
        image = cv2.imread(path)
        if image is None:
            print('Unable to read image %s' % path, file=sys.strderr)
            return False
        texture_loaded = self.loadTextureFromImage(image)

        if not texture_loaded:
            print('Unable to load image %s' % path, file=sys.strderr)

        return texture_loaded

    def generateCheckerboard(self):
        first = [0, 0, 1, 1] * 8
        second = [1, 1, 0, 0] * 8
        checker = [first, first, second, second] * 8
        checkerboard = np.kron(checker, np.ones((8, 8), dtype='uint8'))
        image = np.zeros(
                (checkerboard.shape[0], checkerboard.shape[1], 3),
                dtype='uint8')
        image[:, :, 0] = image[:, :, 1] = image[:, :, 2] = checkerboard.astype(
                'uint8') * 255
        return image

    def freeTexture(self):
        # Delete Texture
        if self.tid != 0:
            gl.glDeleteTextures(1, self.tid)
            self.tid = 0
        self.height = self.width = 0

    def render(self, x, y):
        if self.tid != 0:
            gl.glLoadIdentity()
            gl.glTranslatef(x, y, 0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)

            # Render texture quad
            gl.glBegin(gl.GL_QUADS)
            gl.glTexCoord2f(0, 0)
            gl.glVertex2f(0, 0)
            gl.glTexCoord2f(1, 0)
            gl.glVertex2f(self.width, 0)
            gl.glTexCoord2f(1, 1)
            gl.glVertex2f(self.width, self.height)
            gl.glTexCoord2f(0, 1)
            gl.glVertex2f(0, self.height)
            gl.glEnd()


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.widget = GLWidget(self)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.widget)
        self.setLayout(self.mainLayout)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        super().keyPressEvent(event)


class GLWidget(QtWidgets.QOpenGLWidget):

    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480
    SCREEN_FPS = 60

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

        self.texture = Texture()
        self.loadMedia()

        # initialize projection matrix
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0, -1, 1)

        # Initialize modelview matrix
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # initializeGL clear color
        gl.glClearColor(0, 0, 0, 1)
        gl.glEnable(gl.GL_TEXTURE_2D)

        error = gl.glGetError()
        if error != gl.GL_NO_ERROR:
            print("Error Iniitalizing OpenGL! %s" % glu.gluErrorString(error),
                  file=sys.strderr)
            return False

        return True

    def loadMedia(self):
        return self.texture.loadTextureFromFile(
                os.path.join(os.path.dirname(__file__), 'images', 'atile.jpg'))

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        x = (self.SCREEN_WIDTH - self.texture.width)/2
        y = (self.SCREEN_HEIGHT - self.texture.height)/2
        self.texture.render(x, y)
        gl.glFlush()

    def moveCameraX(self, value):
        self.camera_x += value

    def moveCameraY(self, value):
        self.camera_y += value


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()
