from PySide2 import QtWidgets, QtGui, QtCore
import cv2
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import sys
import array
from ctypes import c_void_p
from enum import Enum

import matplotlib.pyplot as plt


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


class MutableNamedTuple(object):
    __slots__ = []

    def __init__(self, *args):
        for idx, name in enumerate(self.__slots__):
            setattr(self, name, args[idx])

    def __iter__(self):
        for name in self.__slots__:
            yield getattr(self, name)


class Byteable(object):
    typecode = 'f'

    def toarray(self):
        return array.array(self.typecode, self)

    def tobytes(self):
        return self.toarray().tobytes()

    def size(self):
        return len(self.tobytes())


class Rect(MutableNamedTuple):
    __slots__ = ['x', 'y', 'w', 'h']

    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h


class VertexPos2D(MutableNamedTuple, Byteable):
    __slots__ = ['x', 'y']

    def __init__(self, x, y):
        self.x = x
        self.y = y


class TexCoord(MutableNamedTuple, Byteable):
    __slots__ = ['s', 't']

    def __init__(self, s, t):
        self.s = s
        self.t = t


class VertexData(MutableNamedTuple, Byteable):
    __slots__ = ['position', 'tex_coord']

    def __init__(self, position, tex_coord):
        self.position = position
        self.tex_coord = tex_coord

    def toarray(self):
        a = self.position.toarray()
        a.extend(self.tex_coord.toarray())
        return a


class BufferData(list, Byteable):
    def toarray(self):
        if len(self) == 0:
            return array.array('f').tobytes()
        _array = self[0].toarray()
        for obj in self[1:]:
            _array.extend(obj.toarray())
        return _array


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
        self.vboid = 0
        self.iboid = 0

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

            self.initVBO()

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

    def initVBO(self):
        if self.tid != 0 and self.vboid == 0:
            idata = array.array('I', range(4))
            vdata = array.array('f', [0, ] * 16)

            self.vboid = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vboid)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, vdata.tobytes(),
                            gl.GL_DYNAMIC_DRAW)

            self.iboid = gl.glGenBuffers(1)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.iboid)
            gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER, idata.tobytes(),
                            gl.GL_DYNAMIC_DRAW)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def freeVBO(self):
        if self.vboid != 0:
            gl.glDeleteBuffers(self.vboid)
            gl.glDeleteBuffers(self.iboid)
            self.vboid = self.iboid = 0

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

            gl.glTranslatef(x, y, 0)

            vData = BufferData()
            vData.append(VertexData(
                    VertexPos2D(0, 0),
                    TexCoord(tex_left, tex_top)))
            vData.append(VertexData(
                    VertexPos2D(quad_width, 0),
                    TexCoord(tex_right, tex_top)))
            vData.append(VertexData(
                    VertexPos2D(quad_width, quad_height),
                    TexCoord(tex_right, tex_bottom)))
            vData.append(VertexData(
                    VertexPos2D(0, quad_height),
                    TexCoord(tex_left, tex_bottom)))

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vboid)
            gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, vData.tobytes())
            gl.glTexCoordPointer(2, gl.GL_FLOAT, vData[0].size(),
                                 c_void_p(vData[0].position.size()))
            gl.glVertexPointer(2, gl.GL_FLOAT, vData[0].size(), None)

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.iboid)
            gl.glDrawElements(gl.GL_QUADS, 4, gl.GL_UNSIGNED_INT, None)

            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)

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


class SpriteOrigin(Enum):
    SPRITE_ORIGIN_CENTER = 1
    SPRITE_ORIGIN_TOP_LEFT = 2
    SPRITE_ORIGIN_BOTTOM_LEFT = 3
    SPRITE_ORIGIN_TOP_RIGHT = 4
    SPRITE_ORIGIN_BOTTOM_RIGHT = 5


class SpriteSheet(Texture):

    def __init__(self):
        self.vertex_data_buffer = None
        self.index_buffers = None
        self.clips = []
        super().__init__()

    def add_clip_sprite(self, new_clip: Rect):
        self.clips.append(new_clip)
        return len(self.clips)-1

    def get_clip(self, index):
        return self.clips[index]

    def generate_data_buffer(
            self, origin: SpriteOrigin = SpriteOrigin.SPRITE_ORIGIN_CENTER):
        if self.tid != 0 and len(self.clips) > 0:
            totalSprites = len(self.clips)
            self.vertex_data_buffer = gl.glGenBuffers(1)
            self.index_buffers = gl.glGenBuffers(totalSprites)

            top = bottom = left = right = 0

            vtx_data = BufferData()
            for i in range(totalSprites):
                sprite_indices = array.array('I')

                for x in range(4):
                    sprite_indices.append(i*4+x)

                if origin == SpriteOrigin.SPRITE_ORIGIN_TOP_LEFT:
                    top = 0
                    bottom = self.clips[i].h
                    left = 0
                    right = self.clips[i].w
                elif origin == SpriteOrigin.SPRITE_ORIGIN_TOP_RIGHT:
                    top = 0
                    bottom = self.clips[i].h
                    left = -self.clips[i].w
                    right = 0
                elif origin == SpriteOrigin.SPRITE_ORIGIN_BOTTOM_RIGHT:
                    top = -self.clips[i].h
                    bottom = 0
                    left = -self.clips[i].w
                    right = 0
                elif origin == SpriteOrigin.SPRITE_ORIGIN_BOTTOM_LEFT:
                    top = -self.clips[i].h
                    bottom = 0
                    left = 0
                    right = self.clips[i].w
                elif origin == SpriteOrigin.SPRITE_ORIGIN_CENTER:
                    top = -self.clips[i].h // 2
                    bottom = self.clips[i].h // 2
                    left = -self.clips[i].w // 2
                    right = self.clips[i].w // 2 

                # left top
                vtx_data.append(VertexData(
                    VertexPos2D(left, top),
                    TexCoord(self.clips[i].x/self.width,
                             self.clips[i].y/self.height)))

                # right top
                vtx_data.append(VertexData(
                    VertexPos2D(right, top),
                    TexCoord((self.clips[i].x + self.clips[i].w)/self.width,
                             self.clips[i].y/self.height)))

                # right bottom
                vtx_data.append(VertexData(
                    VertexPos2D(right, bottom),
                    TexCoord((self.clips[i].x + self.clips[i].w)/self.width,
                             (self.clips[i].y + self.clips[i].h)/self.height)))

                # left bottom
                vtx_data.append(VertexData(
                    VertexPos2D(left, bottom),
                    TexCoord(self.clips[i].x/self.width,
                             (self.clips[i].y + self.clips[i].h)/self.height)))

                gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER,
                                self.index_buffers[i])
                gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                                sprite_indices.tobytes(), gl.GL_STATIC_DRAW)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_data_buffer)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, vtx_data.tobytes(),
                            gl.GL_STATIC_DRAW)

        else:
            if self.tid == 0:
                print('No textures to render with', file=sys.stderr)
            if len(self.clips) == 0:
                print('No clips to generate vertex data', file=sys.stderr)
            return False
        return True

    def freeSheet(self):
        if self.vertex_data_buffer is not None:
            gl.glDeleteBuffers(np.array([self.vertex_data_buffer]))
            self.vertex_data_buffer = None

        if self.index_buffers is not None:
            gl.glDeleteBuffers(np.array(self.index_buffers))
            self.index_buffers = None

        self.clips.clear()

    def freeTexture(self):
        self.freeSheet()
        super().freeTexture()

    def render_sprite2(self, index):

        import struct
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_data_buffer)
        vdata_bytes = bytes(
                gl.glGetBufferSubData(gl.GL_ARRAY_BUFFER, 0, 64 * 256))

        floats = []
        for x in range(0, len(vdata_bytes), 4):
            floats.extend(struct.unpack('f', vdata_bytes[x: x+4]))

        vData = BufferData()
        for x in range(0, len(floats), 4):
            vData.append(VertexData(
                VertexPos2D(floats[x], floats[x+1]),
                TexCoord(floats[x+2], floats[x+3])))

        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.index_buffers[index])
        idata_bytes = bytes(
                gl.glGetBufferSubData(gl.GL_ELEMENT_ARRAY_BUFFER, 0, 16))
        indices = []
        for x in range(0, len(idata_bytes), 4):
            indices.extend(struct.unpack('I', idata_bytes[x: x+4]))

        gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
        gl.glBegin(gl.GL_QUADS)
        for x in indices:
            gl.glTexCoord2f(*vData[x].tex_coord)
            gl.glVertex2f(*vData[x].position)
        gl.glEnd()

    def render_sprite(self, index):
        if self.vertex_data_buffer is not None:
            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)

            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_data_buffer)
            gl.glTexCoordPointer(2, gl.GL_FLOAT, 16, c_void_p(8))
            gl.glVertexPointer(2, gl.GL_FLOAT, 16, None)

            gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER,
                            self.index_buffers[index])
            gl.glDrawElements(gl.GL_QUADS, 4, gl.GL_UNSIGNED_INT, None)

            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        else:
            print('no buffer has been initialted', file=sys.stderr)


class Font(SpriteSheet):

    def __init__(self):
        self.space = 0
        self.line_height = 0
        self.new_line = 0
        super().__init__()

    def freeFont(self):
        self.freeTexture()

        self.space = 0
        self.line_height = 0
        self.new_line = 0

    def loadBitmap(self, path: str):
        success = True
        black_pixel = (0, 0, 0)

        self.freeFont()

        if self.loadPixelsFromFile(path):
            cellw = self.image_width // 16
            cellh = self.image_width // 16

            top = cellw
            bottom = 0
            a_bottom = 0

            current_char = 0

            # parsing 16 X 16 cells of equal size
            for row in range(16):
                for col in range(16):
                    bx = cellw * col
                    by = cellh * row
                    cell = self.pixels[by:by+cellh, bx:bx+cellw, :]

                    # get cell bounds
                    nonblack = np.any(cell != black_pixel, axis=-1).nonzero()
                    try:
                        left, _top = np.min(nonblack, axis=1)
                        right, _bottom = np.max(nonblack, axis=1)
                    except ValueError:
                        left = right = 0
                        _top, _bottom = cellh, 0

                    next_clip = Rect(bx + left, by,
                                     right - left + 1, cellh)

                    if _top < top:
                        top = _top

                    if ord('A') == current_char:
                        a_bottom = _bottom

                    if _bottom > bottom:
                        bottom = _bottom

                    self.clips.append(next_clip)
                    current_char += 1

            for clip in self.clips:
                clip.y += top
                clip.h -= top

            # Use alpha channel for blending
            pixels = np.zeros((self.pixels.shape[0], self.pixels.shape[1], 4))
            pixels[:, :, 3] = cv2.cvtColor(self.pixels, cv2.COLOR_BGR2GRAY)
            pixels[:, :, 1:3] = 255

            if self.loadTextureFromPixels():
                if not self.generate_data_buffer(
                        SpriteOrigin.SPRITE_ORIGIN_TOP_LEFT):
                    print('Unable to create vertex buffer from pixels',
                          file=sys.stderr)
            else:
                print('Unable to load texture from pixels', file=sys.stderr)

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_BORDER)
            gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                               gl.GL_CLAMP_TO_BORDER)

            self.space = cellw / 2
            self.new_line = a_bottom - top
            self.line_height = bottom - top
        else:
            print('Could not load bitmap font image: %s' % path,
                  file=sys.stderr)
            success = False
        return success

    def renderText(self, x: float, y: float, text: str):
        if self.tid:
            dx, dy = x, y

            gl.glTranslatef(x, y, 0)

            gl.glBindTexture(gl.GL_TEXTURE_2D, self.tid)
            gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
            gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertex_data_buffer)
            vdata = VertexData(VertexPos2D(0, 0), TexCoord(0, 0))
            gl.glTexCoordPointer(2, gl.GL_FLOAT, vdata.size(),
                                 c_void_p(vdata.position.size()))
            gl.glVertexPointer(2, gl.GL_FLOAT, vdata.size(), None)

            for char in text:
                if char == ' ':
                    gl.glTranslatef(self.space, 0, 0)
                    dx += self.space
                elif char == '\n':
                    gl.glTranslatef(x-dx, self.new_line, 0)
                    dy += self.new_line
                    dx += x - dx
                else:
                    ascii_code = ord(char)
                    gl.glBindBuffer(
                            gl.GL_ELEMENT_ARRAY_BUFFER,
                            self.index_buffers[ascii_code])
                    gl.glDrawElements(gl.GL_QUADS, 4, gl.GL_UNSIGNED_INT, None)
                    gl.glTranslatef(self.clips[ascii_code].w, 0, 0)
                    dx += self.clips[ascii_code].w

            gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
            gl.glDisableClientState(gl.GL_VERTEX_ARRAY)


class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
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
        self.sprites = SpriteSheet()
        self.font = Font()
        self.texX = self.texY = 0
        self._wraptype = 0
        # self.start_timer()
        self.quad_vertices = array.array('f')
        self.indices = array.array('I')
        self.vertex_buffer = 0
        self.index_buffer = 0
        array.typecodes

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
        if self._wraptype >= 5:
            self._wraptype = 0

        if self._wraptype == 0:
            self.texture.default_texture_wrap = gl.GL_REPEAT
        elif self._wraptype == 1:
            self.texture.default_texture_wrap = gl.GL_CLAMP
        elif self._wraptype == 2:
            self.texture.default_texture_wrap = gl.GL_CLAMP_TO_BORDER
        elif self._wraptype == 3:
            self.texture.default_texture_wrap = gl.GL_CLAMP_TO_EDGE
        elif self._wraptype == 4:
            self.texture.default_texture_wrap = gl.GL_MIRRORED_REPEAT

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
        if not self.font.loadBitmap('images/cells.png'):
            print('Unable to load bitmap image', file=sys.stderr)
            return False
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
        gl.glClearColor(0, 0, 0, 0)
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

    def paintGL(self):

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glLoadIdentity()

        gl.glColor3f(1, 0, 0)
        self.font.renderText(
                0, 0, 'The quick brown fox jumps\nover the lazy dog')

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
