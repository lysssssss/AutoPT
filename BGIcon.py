import wx
import wx.adv
from wx.lib.pubsub import pub

import Myconfig
import Mylogger
import globalvar as gl


# class ClockWindow(wx.Window):
#     def __init__(self):
#         wx.Window.__init__(self)
#         self.logger = gl.get_value('logger').logger
#         self.timer = wx.Timer(self)
#         self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
#         self.timer.Start(1000)
#
#     def OnTimer(self, event):
#         if gl.get_value('thread') is not None and gl.get_value('thread').is_alive():
#             pass
#         else:
#             self.logger.info('检测到线程关闭，异常退出')
#             wx.MessageBox('检测到异常线程关闭', "AutoPT")
#             wx.Exit()


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
        self.windowhandler.Raise()
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


class LoginFrame(wx.Dialog):
    def __init__(self, station, image, loginflag, windowhandler):
        wx.Dialog.__init__(self, parent=None, id=2, title='登录' + station, pos=wx.DefaultPosition,
                           size=(370, 230), style=wx.CAPTION | wx.CLOSE_BOX, name='login')
        self.loginflag = loginflag

        # 拉起日志窗口
        windowhandler.Raise()

        # 利用wxpython的GridBagSizer()进行页面布局
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(10, 20)  # 列间隔为10，行间隔为20

        # 添加账号字段，并加入页面布局，为第一行，第一列
        text = wx.StaticText(panel, label="用户名")
        sizer.Add(text, pos=(0, 0), flag=wx.ALL, border=5)

        # 添加文本框字段，并加入页面布局，为第一行，第2,3列
        self.tc = wx.TextCtrl(panel)
        sizer.Add(self.tc, pos=(0, 1), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5)

        # 添加密码字段，并加入页面布局，为第二行，第一列
        text1 = wx.StaticText(panel, label="密码")
        sizer.Add(text1, pos=(1, 0), flag=wx.ALL, border=5)

        # 添加文本框字段，以星号掩盖,并加入页面布局，为第二行，第2,3列
        self.tc1 = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
        sizer.Add(self.tc1, pos=(1, 1), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5)

        # 添加验证码字段，并加入页面布局，为第三行，第一列
        text2 = wx.StaticText(panel, label="验证码")
        sizer.Add(text2, pos=(2, 0), flag=wx.ALL, border=5)

        # 添加文本框字段，并加入页面布局，为第三行，第2列
        self.tc2 = wx.TextCtrl(panel)
        sizer.Add(self.tc2, pos=(2, 1), flag=wx.ALL, border=5)

        # 添加验证码图片，并加入页面布局，为第三行，第3列
        # image = wx.Image(image, wx.BITMAP_TYPE_ANY).Rescale(80, 25).ConvertToBitmap()  # 获取图片，转化为Bitmap形式
        image = image.resize((int(80*1.7), int(25*1.7)))
        image = wx.Bitmap.FromBuffer(image.size[0], image.size[1], image.tobytes())
        self.bmp = wx.StaticBitmap(panel, -1, image)  # 转化为wx.StaticBitmap()形式
        sizer.Add(self.bmp, pos=(2, 2), flag=wx.ALL, border=5)

        # 添加登录按钮，并加入页面布局，为第四行，第2列
        btn = wx.Button(panel, -1, "登录")
        sizer.Add(btn, pos=(3, 1), flag=wx.ALL, border=5)

        # 为登录按钮绑定login_process事件
        self.Bind(wx.EVT_BUTTON, self.getlogindata, btn)
        # 将Panmel适应GridBagSizer()放置
        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_CLOSE, self.onExit)  # 绑定“退出”选项的点击事件

    def getlogindata(self, event):
        if self.tc1.GetValue() == '' or self.tc2.GetValue() == '' or self.tc.GetValue() == '':
            wx.MessageBox('用户名密码验证码不能为空', "Error")
            return
        gl.set_value('logindata', [self.tc1.GetValue(), self.tc2.GetValue(), self.tc.GetValue(), True])
        self.loginflag[0] = True
        self.Close()

    def onExit(self, event):
        if not self.loginflag[0]:
            gl.set_value('logindata', ['', '', '', False])
            self.loginflag[0] = True
        self.Destroy()


class MyFrame(wx.Frame):
    ICON = "logo.ico"  # 图标地址

    def __init__(self):
        wx.Frame.__init__(self, parent=None, id=1, title='AutoPT', pos=wx.DefaultPosition,
                          size=(1000, 700), style=wx.CAPTION | wx.CLOSE_BOX, name='frame')

        self.SetIcon(wx.Icon(self.ICON))  # 设置图标和标题

        self.SetForegroundColour(wx.WHITE)
        self.SetBackgroundColour(wx.WHITE)

        self.textctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)

        self.textctrl.SetForegroundColour(wx.BLACK)
        self.textctrl.SetBackgroundColour(wx.WHITE)

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
        self.logger = gl.get_value('logger').logger
        # list是为了引用传参
        self.loginflag = [False]
        wx.App.__init__(self, redirect, filename)

    def OnInit(self):
        self.frame = MyFrame()
        self.TaskBar = MyTaskBarIcon(self.frame)  # 显示系统托盘图标
        # self.timer = ClockWindow()
        gl.set_value('logwindow', self.frame)
        self.SetTopWindow(self.frame)
        self.frame.Show()
        wx.FutureCall(1000, self.checkptthread)
        pub.subscribe(self.updateHandle, "update")
        return True

    def checkptthread(self):
        if gl.get_value('thread') is not None and gl.get_value('thread').is_alive():
            # time.sleep(1)
            wx.FutureCall(1000, self.checkptthread)
        else:
            self.logger.info('检测到线程关闭，异常退出')
            self.frame.Show()
            wx.MessageBox('检测到异常线程关闭', "AutoPT")
            wx.Exit()

    def updateHandle(self, msg):
        frame = LoginFrame(msg[0], msg[1], self.loginflag, self.frame)
        frame.ShowModal()

    def getlogindata(self, title='', image=None):
        self.loginflag = [False]
        wx.CallAfter(pub.sendMessage, "update", msg=[title, image])
        while not self.loginflag[0]:
            pass
        pass


if __name__ == "__main__":
    gl._init()
    gl.set_value('config', Myconfig.Config())
    gl.set_value('logger', Mylogger.Mylogger())
    app = MyApp()
    app.MainLoop()
