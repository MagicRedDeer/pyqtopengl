from PySide2 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import sys
import os


class Rect(object):
    __slots__ = ['x', 'y', 'w', 'h']

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class Texture(object):

    def __init__(self):
        self.tid = 0
        self.width = 0
        self.height = 0
        self.pixels = None
        self.channels = 0

    def loadTextureFromImage(self, image: np.array):
        pixel_type = gl.GL_BGRA
        store_type = gl.GL_RGBA

        self.channels = image.shape[2] if len(image.shape) > 2 else 1
        assert(self.channels in (3, 4))
        if self.channels == 3:
            pixel_type = gl.GL_BGR
            store_type = gl.GL_RGB

        self.height = image.shape[0]
        self.width = image.shape[1]

        self.tid = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, self.tid)

        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, store_type, self.width,
                        self.height, 0, pixel_type, gl.GL_UNSIGNED_BYTE, image)

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

    def loadTextureFromFile(self, path, ignore_alpha=False):

        args = [path]
        if not ignore_alpha:
            args.append(cv2.IMREAD_UNCHANGED)

        image = cv2.imread(*args)
        if image is None:
            print('Unable to read image %s' % path, file=sys.stderr)
            return False

        texture_loaded = self.loadTextureFromImage(image)
        if not texture_loaded:
            print('Unable to load image %s' % path, file=sys.stderr)

        return texture_loaded

    def freeTexture(self):
        # Delete Texture
        if self.tid != 0:
            gl.glDeleteTextures(1, self.tid)
            self.tid = 0
        self.pixels = None
        self.height = self.width = 0

    def render(self, x, y, clip: Rect = None):
        if self.tid != 0:
            gl.glLoadIdentity()
            gl.glTranslatef(x, y, 0)

            tex_top = tex_left = 0.0
            tex_bottom = tex_right = 1.0
            quad_width, quad_height = self.width, self.height

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

    def lock(self):
        if self.pixels is None and self.tid != 0:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            self.pixels = gl.glGetTexImage(
                    gl.GL_TEXTURE_2D, 0, gl.GL_BGRA, gl.GL_UNSIGNED_BYTE)
            self.pixels = np.frombuffer(self.pixels, dtype='uint8').reshape(
                    self.width, self.height, self.channels)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
            return True
        return False

    def unlock(self):
        if self.pixels is not None and self.tid != 0:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            gl.glTexSubImage2D(
                    gl.GL_TEXTURE_2D, 0, 0, 0, self.width, self.height,
                    gl.GL_BGRA, gl.GL_UNSIGNED_BYTE, self.pixels)
            self.pixels = np.array(self.pixels)
            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


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

    def loadMedia(self):
        if not self.texture.loadTextureFromFile(
                os.path.join(
                    os.path.dirname(__file__), 'images', 'circle.png')):
            print('Unable to load circle texture', file=sys.stderr)

        self.texture.lock()

        pixels = self.texture.pixels
        alpha = pixels[:, :, 3].copy()

        for x in range(10,
                       min(self.texture.width//2, self.texture.height//2), 10):
            pixels = cv2.rectangle(
                    pixels,
                    (self.texture.height//2-x, self.texture.width//2-x),
                    (self.texture.height//2+x, self.texture.width//2+x),
                    (255, 0, 0, 255), 2)

        pixels = cv2.bitwise_and(pixels, pixels, mask=alpha)

        self.texture.pixels = pixels
        self.texture.unlock()

        return True

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

    def quad_vertices(self):
        gl.glVertex2f(-self.SCREEN_WIDTH//4, -self.SCREEN_HEIGHT//4)
        gl.glVertex2f(self.SCREEN_WIDTH//4, -self.SCREEN_HEIGHT//4)
        gl.glVertex2f(self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4)
        gl.glVertex2f(-self.SCREEN_WIDTH//4, self.SCREEN_HEIGHT//4)

    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        self.texture.render(self.SCREEN_WIDTH/2-self.texture.width/2,
                            self.SCREEN_HEIGHT/2-self.texture.height/2)

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
