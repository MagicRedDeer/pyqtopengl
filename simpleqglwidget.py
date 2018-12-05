from OpenGL.GL import *
from OpenGL.GLU import *

from PySide2 import QtWidgets

class MainWindow(QtWidgets.QWidget):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.button = QtWidgets.QPushButton('Test', self)

        self.widget = GLWidget(self)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.widget)
        self.mainLayout.addWidget(self.button)

        self.setLayout(self.mainLayout)


class GLWidget(QtWidgets.QOpenGLWidget):

    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(640, 480)

    def initializeGL(self) -> None:

        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, 1.33, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(-2.5, 0.5, -6.0)
        glColor3f(1.0, 1.5, 0.0)
        glPolygonMode(GL_FRONT, GL_FILL)

        glBegin(GL_TRIANGLES)
        glVertex3f(2.0, -1.2, 0.0)
        glVertex3f(2.6, 0.0, 0.0)
        glVertex3f(2.9, -1.2, 0.0)
        glEnd()

        glColor3f(0.0, 1.5, 1.0)
        glBegin( GL_QUADS )
        glVertex2f( -0.5, -0.5 )
        glVertex2f( 0.5, -0.5 )
        glVertex2f( 0.5, 0.5 )
        glVertex2f( -0.5, 0.5 )
        glEnd();


        glFlush()

if __name__ == "__main__":
    app = QtWidgets.QApplication(['Hey Hey'])
    window = MainWindow()
    window.show()
    app.exec_()
