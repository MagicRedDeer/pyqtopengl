from PySide2 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import sys
import os


def power_of_two(num: int):
    if num != 0:
        num -= 1
        num |= (num >> 1)   # Or first 2 bits
        num |= (num >> 2)   # Or next 2 bits
        num |= (num >> 4)   # Or next 4 bits
        num |= (num >> 8)   # Or next 8 bits
        num |= (num >> 16)  # Or next 16 bits
        num += 1
    return num


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
        self.image_width = 0
        self.image_height = 0
        self.filtering = gl.GL_LINEAR
        self.default_texture_wrap = gl.GL_REPEAT

    def loadTextureFromPixels(self):
        if self.tid == 0 and self.pixels is not None:
            self.height = self.pixels.shape[0]
            self.width = self.pixels.shape[1]

            self.tid = gl.glGenTextures(1)
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, self.tid)

            gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, self.store_type, self.width,
                            self.height, 0, self.pixel_type,
                            gl.GL_UNSIGNED_BYTE, self.pixels)

            self.applyTextureFiltering(bind=False)

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

    def loadTextureFromFile(self, path, with_alpha=True):
        if not self.loadPixelsFromFile(path, with_alpha=with_alpha):
            return False
        return self.loadTextureFromPixels()

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
                power_of_two(self.pixels.shape[0]) - self.pixels.shape[0],
                0,
                power_of_two(self.pixels.shape[1]) - self.pixels.shape[1],
                cv2.BORDER_CONSTANT, value=(255, 0, 0))

        return True

    def loadTextureFromFileWithColorKey(
            self, path, color_key=(0, 0, 0, 255)):
        if not self.loadPixelsFromFile(path):
            return False

        np.where(self.pixels == color_key, (0, 0, 0, 0), self.pixels)
        cv2.bitwise_and(self.pixels, self.pixels, mask=self.pixels[:, :, 3])

        return self.loadTextureFromPixels()

    def freeTexture(self):
        # Delete Texture
        if self.tid != 0:
            gl.glDeleteTextures(1, self.tid)
            self.tid = 0
        self.pixels = None
        self.height = self.width = 0
        self.image_height = self.image_height = 0

    def render(self, x, y, clip: Rect = None):
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

            gl.glTranslatef(x + quad_width/2, y + quad_height/2, 0)

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

    def applyTextureFiltering(self, bind=True):
        if bind:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                self.filtering)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                self.filtering)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                self.default_texture_wrap)
        gl.glTexParameteri(
                gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                self.default_texture_wrap)
        if bind:
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

            self.widget.wrap_type += 1

        super().keyPressEvent(event)


class GLWidget(QtWidgets.QOpenGLWidget):

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    SCREEN_FPS = 600

    def __init__(self, parent):
        super().__init__(parent)
        self.texture = Texture()
        self.texX = self.texY = 0
        self._wraptype = 0
        self.start_timer()

    def update(self):
        self.texX += 1
        self.texY += 1

        if self.texX >= self.texture.width:
            self.texX = 0
        if self.texY >= self.texture.height:
            self.texY = 0

        super().update()

    @property
    def wrap_type(self):
        return self._wraptype

    @wrap_type.setter
    def wrap_type(self, value):
        self._wraptype = value
        if self._wraptype >= 2:
            self._wraptype = 0

        if self._wraptype == 0:
            self.texture.default_texture_wrap = gl.GL_REPEAT
        else:
            self.texture.default_texture_wrap = gl.GL_CLAMP

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
        if not self.texture.loadTextureFromFile(os.path.join(
                os.path.dirname(__file__), 'images', 'tapestry.bmp')):
            print('Failed to load media', file=sys.stderr)
        return True

    def initializeGL(self):
        print(self.getOpenglInfo())

        self.loadMedia()

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

        texture_right = self.SCREEN_WIDTH / self.texture.width
        texture_bottom = self.SCREEN_HEIGHT / self.texture.width

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.texture.tid)

        self.texture.applyTextureFiltering(bind=False)

        gl.glMatrixMode(gl.GL_TEXTURE)
        gl.glLoadIdentity()

        gl.glTranslatef(self.texX / self.texture.width,
                        self.texY / self.texture.height, 0)

        gl.glBegin(gl.GL_QUADS)

        gl.glTexCoord2f(0, 0)
        gl.glVertex2f(0, 0)
        gl.glTexCoord2f(texture_right, 0)
        gl.glVertex2f(self.SCREEN_WIDTH, 0)
        gl.glTexCoord2f(texture_right, texture_bottom)
        gl.glVertex2f(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        gl.glTexCoord2f(0, texture_bottom)
        gl.glVertex2f(0, self.SCREEN_HEIGHT)

        gl.glEnd()

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
