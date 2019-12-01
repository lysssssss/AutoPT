import wx
import wx.adv

import Myconfig
import Mylogger
import globalvar as gl


class ClockWindow(wx.Window):
    def __init__(self):
        wx.Window.__init__(self)
        self.logger = gl.get_value('logger').logger
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000)

    def OnTimer(self, event):
        if gl.get_value('thread').is_alive():
            pass
        else:
            self.logger.info('检测到线程关闭，异常退出')
            wx.Exit()


class MyTaskBarIcon(wx.adv.TaskBarIcon):
    ICON = "logo.ico"  # 图标地址
    ID_ABOUT = wx.NewIdRef(count=1)  # 菜单选项“关于”的ID
    ID_EXIT = wx.NewIdRef(count=1)  # 菜单选项“退出”的ID
    ID_SHOW_LOG = wx.NewIdRef(count=1)  # 菜单选项“显示页面”的ID
    TITLE = "Auto download PT torrent"  # 鼠标移动到图标上显示的文字

    def __init__(self, windowhandler):
        wx.adv.TaskBarIcon.__init__(self)
        self.logger = gl.get_value('logger').logger
        self.SetIcon(wx.Icon(self.ICON), self.TITLE)  # 设置图标和标题
        self.Bind(wx.EVT_MENU, self.onAbout, id=self.ID_ABOUT)  # 绑定“关于”选项的点击事件
        self.Bind(wx.EVT_MENU, self.onExit, id=self.ID_EXIT)  # 绑定“退出”选项的点击事件
        self.Bind(wx.EVT_MENU, self.onShowLog, id=self.ID_SHOW_LOG)  # 绑定“显示页面”选项的点击事件
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.onShowLog)  # 绑定“显示页面”选项的点击事件
        self.windowhandler = windowhandler

    # “关于”选项的事件处理器
    def onAbout(self, event):
        self.logger.debug('菜单关于 点击事件')
        wx.MessageBox('程序作者：LYS\n最后更新日期：2019年12月1日', "关于")

    # “退出”选项的事件处理器
    def onExit(self, event):
        self.logger.debug('菜单退出 点击事件')
        wx.Exit()

    # “显示页面”选项的事件处理器
    def onShowLog(self, event):
        self.logger.debug('菜单显示 点击事件')
        self.windowhandler.Show()
        pass

    # 创建菜单选项
    def CreatePopupMenu(self):
        menu = wx.Menu()
        for mentAttr in self.getMenuAttrs():
            menu.Append(mentAttr[1], mentAttr[0])
        return menu

    # 获取菜单的属性元组
    def getMenuAttrs(self):
        return [('进入程序', self.ID_SHOW_LOG),
                ('关于', self.ID_ABOUT),
                ('退出', self.ID_EXIT)]


class MyFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=1, title='AutoPT', pos=wx.DefaultPosition,
                          size=(800, 600), style=wx.CAPTION | wx.CLOSE_BOX, name='frame')

        self.textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE)

        self.Bind(wx.EVT_CLOSE, self.onExit)  # 绑定“退出”选项的点击事件

        self.logger = gl.get_value('logger').logger

    def onExit(self, event):
        self.logger.debug('窗口隐藏事件')
        self.Hide()


class MyApp(wx.App):
    def __init__(self, redirect=False, filename=None):
        self.frame = None
        self.TaskBar = None
        self.timer = None
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = MyFrame()
        self.TaskBar = MyTaskBarIcon(self.frame)  # 显示系统托盘图标
        self.timer = ClockWindow()
        gl.set_value('logwindow', self.frame)
        # self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


if __name__ == "__main__":
    gl._init()
    gl.set_value('config', Myconfig.Config())
    gl.set_value('logger', Mylogger.Mylogger())
    app = MyApp()
    app.MainLoop()
