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
        self.pixels = None
        self.channels = 0
        self.image_width = 0
        self.image_height = 0
        self.filtering = gl.GL_LINEAR

    def loadTextureFromNP(self):
        if self.tid == 0 and self.pixels is not None:
            self.height = self.pixels.shape[0]
            self.width = self.pixels.shape[1]

            self.tid = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, self.tid)

            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, self.store_type, self.width,
                            self.height, 0, self.pixel_type,
                            gl.GL_UNSIGNED_BYTE, self.pixels)

            gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, self.filtering)
            gl.glTexParameteri(
                    gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, self.filtering)

            gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

            error = gl.glGetError()
            if error != gl.GL_NO_ERROR:
                print('Error loading pixels from image! %s' %
                      glu.gluErrorString(error), file=sys.stderr)
                return False

        else:
            print('Cannot load texture from current pixels', file=sys.stderr)
            if self.tid != 0:
                print('A texture is already loaded', file=sys.stderr)
            elif self.pixels is None:
                print('No pixels to create Textures from!', file=sys.stderr)
            return False

        return True

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

    def loadTextureFromFile(self, path, with_alpha=True):
        if not self.loadPixelsFromFile(path, with_alpha=with_alpha):
            return False
        return self.loadTextureFromNP()

    def loadPixelsFromFile(self, path, with_alpha=True):
        self.pixels = cv2.imread(
                path,
                cv2.IMREAD_UNCHANGED if with_alpha else cv2.IMREAD_COLOR)

        if self.pixels is None:
            print('Unable to load image from %s' % path, file=sys.stderr)
            return False

        self.channels = self.pixels.shape[2] if len(
                self.pixels.shape) > 2 else 1

        if self.channels not in (3, 4):
            print('Given image is not supported')
            return False

        if self.channels == 3:
            self.pixel_type = gl.GL_BGR
            self.store_type = gl.GL_RGB
        elif self.channels == 4:
            self.pixel_type = gl.GL_BGRA
            self.store_type = gl.GL_RGBA

        self.image_height = self.pixels.shape[0]
        self.image_width = self.pixels.shape[1]

        self.pixels = cv2.copyMakeBorder(
                self.pixels,
                0,
                self.power_of_two(self.pixels.shape[0]) - self.pixels.shape[0],
                0,
                self.power_of_two(self.pixels.shape[1]) - self.pixels.shape[1],
                cv2.BORDER_CONSTANT, value=0)

        return True

    def loadTextureFromFileWithColorKey(
            self, path, color_key=(0, 0, 0, 255)):
        if not self.loadPixelsFromFile(path):
            return False

        np.where(self.pixels == color_key, (0, 0, 0, 0), self.pixels)
        cv2.bitwise_and(self.pixels, self.pixels, mask=self.pixels[:, :, 3])

        return self.loadTextureFromNP()

    def loadMedia(self):
        if not self.loadTextureFromFile(os.path.join(
                os.path.dirname(__file__), 'images', 'arrow.png')):
            print('Failed to load media', file=sys.stderr)
        return True

    def freeTexture(self):
        # Delete Texture
        if self.tid != 0:
            gl.glDeleteTextures(1, self.tid)
            self.tid = 0
        self.pixels = None
        self.height = self.width = 0
        self.image_height = self.image_height = 0

    def render(self, x, y, clip: LFRect = None, stretch: LFRect = None,
               degrees=0):
        if self.tid != 0:
            self.applyTextureFiltering()

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

            if stretch is not None:
                quad_width, quad_height = stretch.w, stretch.h

            gl.glLoadIdentity()
            gl.glTranslatef(x + quad_width/2, y + quad_height/2, 0)
            gl.glRotatef(degrees, 0, 0, 1)

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)

            # Render texture quad
            gl.glBegin(gl.GL_QUADS)

            gl.glTexCoord2f(tex_left, tex_top)
            gl.glVertex2f(-quad_width/2, -quad_height/2)

            gl.glTexCoord2f(tex_right, tex_top)
            gl.glVertex2f(quad_width/2, -quad_height/2)

            gl.glTexCoord2f(tex_right, tex_bottom)
            gl.glVertex2f(quad_width/2, quad_height/2)

            gl.glTexCoord2f(tex_left, tex_bottom)
            gl.glVertex2f(-quad_width/2, quad_height/2)

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

    def applyTextureFiltering(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                self.filtering)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                self.filtering)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.button = QtWidgets.QPushButton('Test', self)
        self.widget = GLWidget(self)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.widget)
        self.setLayout(self.mainLayout)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Q:

            if self.widget.texture.filtering != gl.GL_LINEAR:
                self.widget.texture.filtering = gl.GL_LINEAR
                print('linear filtering')
            else:
                self.widget.texture.filtering = gl.GL_NEAREST
                print('nearest filtering')

        super().keyPressEvent(event)


class GLWidget(QtWidgets.QOpenGLWidget):

    SCREEN_WIDTH = 640
    SCREEN_HEIGHT = 480
    SCREEN_FPS = 60

    stretch_rect = LFRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
    angle = 0

    def __init__(self, parent):
        super().__init__(parent)
        self.start_timer()

    def update(self):
        self.angle += 360 / self.SCREEN_FPS
        if self.angle > 360:
            self.angle -= 360
        super().update()

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
        gl.glClearColor(0, 1, 0, 1)
        gl.glEnable(gl.GL_TEXTURE_2D)

        # Set blending
        gl.glEnable(gl.GL_BLEND)
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

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
                            self.SCREEN_HEIGHT/2-self.texture.image_height/2,
                            degrees=self.angle)

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
