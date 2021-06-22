# -*- coding: utf-8 -*-
import sys
import time
import threading
import numpy as np
from numba import jit

from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg

from rasp_audio_stream import AudioInputStream


# 絶対値計算
def calc_rad(x, y, rad, length):
    rad[:] = np.sqrt((x[:]**2 + y[:]**2)* 0.5)
    
# 偏角計算
@jit
def calc_arg(x, y, phase, length):
    eps = 1e-16
    phase[:] = np.arctan(y/(x+eps))
    for k in range(length):
        if     (x[k] < 0 and y[k] > 0) \
            or (x[k] < 0 and y[k] < 0):
            phase[k] += np.pi
        elif   (x[k] > 0 and y[k] < 0):
            phase[k] += 2*np.pi
        if x[k] == 0:
            phase[k] = np.pi/2 if y[k] > 0 else 3*np.pi/2
        elif y[k] == 0: 
            phase[k] = 0 if x[k] > 0 else np.pi


# 散布図プロット用クラス
class PQGPhaseScope():
    def __init__(self,
                 sig_shape,
                 fps=60, 
                 xrange=[-1, 1], 
                 yrange=[-1, 1],
                 size=(500,500), 
                 title=""
        ):
        if sig_shape[0] != 2: # ステレオ信号であるかチェック
            return 
        self.n_ch, self.length = sig_shape    
         
        # PyQtGraph 散布図の初期設定
        app = QtGui.QApplication([]) 
        win = pg.GraphicsLayoutWidget()
        win.resize(size[0], size[1])
        win.show()
        plotitem     = win.addPlot(title=title)
        plotdataitem = plotitem.plot(pen=None, symbol="o", symbolPen='b', symbolSize=10, symbolBrush='c') 
        pg.setConfigOptions(antialias=True)

        plotitem.setXRange(xrange[0], xrange[1])
        plotitem.setYRange(yrange[0], yrange[1])
        plotitem.showGrid(x = True, y = True, alpha = 0.3)
        
        # インスタンス変数
        self.app          = app
        self.win          = win
        self.plotitem     = plotitem
        self.plotdataitem = plotdataitem
        
        self.sig = np.zeros(sig_shape)   # 変数格納用
        self.fps = fps
        
    def run_app(self):
        # 一定時間ごとにupdate実行
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(1/self.fps * 1000)
        
        # GUIアプリ起動
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def update(self):
        # 保持している信号を取り出す
        y, x = self.sig[0], self.sig[1]
        
        # 絶対値・偏角の算出
        rad   = np.zeros(self.length)
        phase = np.zeros(self.length)
        calc_rad(x, y, rad,   self.length)
        calc_arg(x, y, phase, self.length)
        
        # 値をいい感じに調整
        rad **= 0.5
        phase += 0.25 * np.pi
        
        alpha = np.mean(rad)**2
        alpha_max = 0.2
        alpha = alpha_max if alpha_max > 0.2 else alpha
        
        # 散布図に表示するデータ点の直交座標算出
        x_mod = rad*np.cos(phase)
        y_mod = rad*np.sin(phase)
        
        # 現在のデータ点での透明度設定
        self.plotdataitem.setAlpha(alpha, False)
        # 現在のデータ点で描画
        self.plotdataitem.setData(x_mod, y_mod)

    
    def callback_sigproc(self, sig):
        # PyAudioでのコールバック用
        self.sig[:] = sig
