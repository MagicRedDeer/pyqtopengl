from PySide2 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import sys
import os
from collections import namedtuple


LFRect = namedtuple('LFRect', 'x y w h')


class Texture(object):

    def __init__(self):
        self.tid = 0
        self.width = 0
        self.height = 0
        self.image_height = 0
        self.image_width = 0

    def power_of_two(self, num: int):
        if num != 0:
            num -= 1
            num |= (num >> 1)   # Or first 2 bits
            num |= (num >> 2)   # Or next 2 bits
            num |= (num >> 4)   # Or next 4 bits
            num |= (num >> 8)   # Or next 8 bits
            num |= (num >> 16)  # Or next 16 bits
            num += 1
        return num

    def loadTextureFromNumpyRGBImage(self, image: np.array):

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

        self.image_height = image.shape[0]
        self.image_width = image.shape[1]

        texture = cv2.copyMakeBorder(
                image,
                0, self.power_of_two(self.image_width) - self.image_width,
                0, self.power_of_two(self.image_height) - self.image_height,
                cv2.BORDER_CONSTANT, value=0)

        texture_loaded = self.loadTextureFromNumpyRGBImage(texture)

        if not texture_loaded:
            print('Unable to load image %s' % path, file=sys.strderr)

        return texture_loaded

    def loadMedia(self):
        return self.loadTextureFromFile(
                os.path.join(os.path.dirname(__file__),
                             'images', 'opengl.jpg'))

    def freeTexture(self):
        # Delete Texture
        if self.tid != 0:
            gl.glDeleteTextures(np.array([self.tid]))
            self.tid = 0
        self.height = self.width = 0
        self.image_height = self.image_width = 0

    def render(self, x, y, clip: LFRect = None):
        if self.tid != 0:
            gl.glLoadIdentity()
            gl.glTranslatef(x, y, 0)

            tex_top = tex_left = 0.0
            tex_bottom = self.image_height / self.height
            tex_right = self.image_width / self.width

            quad_width, quad_height = self.image_width, self.image_height

            if clip is not None:
                tex_left = clip.x / self.width
                tex_right = (clip.x + clip.w) / self.width
                tex_top = clip.y / self.height
                tex_bottom = (clip.y + clip.h) / self.height
                quad_width, quad_height = clip.w, clip.h

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)

            # Render texture quad
            gl.glBegin(gl.GL_QUADS)

            gl.glTexCoord2f(tex_left, tex_top)
            gl.glVertex2f(0, 0)

            gl.glTexCoord2f(tex_right, tex_top)
            gl.glVertex2f(quad_width, 0)

            gl.glTexCoord2f(tex_right, tex_bottom)
            gl.glVertex2f(quad_width, quad_height)

            gl.glTexCoord2f(tex_left, tex_bottom)
            gl.glVertex2f(0, quad_height)

            gl.glEnd()


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.button = QtWidgets.QPushButton('Test', self)
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
        # self.start_timer()

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
        self.texture.loadMedia()

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

    def quad_vertices(self):
        gl.glVertex2f(-self.SCREEN_WIDTH//4, -self.SCREEN_HEIGHT//4)
        gl.glVertex2f(self.SCREEN_WIDTH//4, -self.SCREEN_HEIGHT//4)
        gl.glVertex2f(self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4)
        gl.glVertex2f(-self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.texture.render(self.SCREEN_WIDTH/2-self.texture.image_width/2,
                            self.SCREEN_HEIGHT/2-self.texture.image_height/2)

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
