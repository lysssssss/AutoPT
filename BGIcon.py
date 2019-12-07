import datetime

import wx
import wx.adv
from pubsub import pub

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
    TITLE = "AutoPT"  # 鼠标移动到图标上显示的文字

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
        self.windowhandler.Hide()
        self.logger.debug('菜单退出 点击事件')
        # 退出时记得把logger的句柄移除，否则永远卡死在handler的emit里
        self.logger.removeHandler(gl.get_value('logger').loggingRedirectHandler)
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
                           size=(380, 230), style=wx.CAPTION | wx.CLOSE_BOX, name='login')
        self.loginflag = loginflag

        # 拉起日志窗口
        windowhandler.Raise()

        # 利用wxpython的GridBagSizer()进行页面布局
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 10)  # 列间隔为10，行间隔为20

        # 添加账号字段，并加入页面布局，为第一行，第一列
        text = wx.StaticText(panel, label="用户名")
        sizer.Add(text, pos=(0, 0), flag=wx.ALL, border=5)

        # 添加文本框字段，并加入页面布局，为第一行，第2,3列
        self.textinput_user = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        sizer.Add(self.textinput_user, pos=(0, 1), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5)
        self.Bind(wx.EVT_TEXT_ENTER, self.getlogindata, self.textinput_user)

        # 添加密码字段，并加入页面布局，为第二行，第一列
        text1 = wx.StaticText(panel, label="密码")
        sizer.Add(text1, pos=(1, 0), flag=wx.ALL, border=5)

        # 添加文本框字段，以星号掩盖,并加入页面布局，为第二行，第2,3列
        self.textinput_pwd = wx.TextCtrl(panel, style=wx.TE_PASSWORD | wx.TE_PROCESS_ENTER)
        sizer.Add(self.textinput_pwd, pos=(1, 1), span=(1, 2), flag=wx.EXPAND | wx.ALL, border=5)
        self.Bind(wx.EVT_TEXT_ENTER, self.getlogindata, self.textinput_pwd)

        if image is not None:
            # 添加验证码字段，并加入页面布局，为第三行，第一列
            text2 = wx.StaticText(panel, label="验证码")
            sizer.Add(text2, pos=(2, 0), flag=wx.ALL, border=5)

            # 添加文本框字段，并加入页面布局，为第三行，第2列
        self.textinput_captcha = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)

        if image is not None:
            sizer.Add(self.textinput_captcha, pos=(2, 1), flag=wx.ALL, border=5)
            self.Bind(wx.EVT_TEXT_ENTER, self.getlogindata, self.textinput_captcha)

            # 添加验证码图片，并加入页面布局，为第三行，第3列
            # image = wx.Image(image, wx.BITMAP_TYPE_ANY).Rescale(80, 25).ConvertToBitmap()  # 获取图片，转化为Bitmap形式
            # image = image.resize((int(image.size[0]/2), int(image.size[1]/2)))
            image = wx.Bitmap.FromBuffer(image.size[0], image.size[1], image.tobytes())
            self.bmp = wx.StaticBitmap(panel, -1, image)  # 转化为wx.StaticBitmap()形式
            sizer.Add(self.bmp, pos=(2, 2), flag=wx.ALL, border=5)
        else:
            # 不需要验证码，随便填一个
            self.textinput_captcha.Hide()
            self.textinput_captcha.SetValue('invalid')

        # 添加登录按钮，并加入页面布局，为第四行，第2列
        btn = wx.Button(panel, -1, "登录")
        sizer.Add(btn, pos=(3, 1), flag=wx.ALL, border=5)

        # 为登录按钮绑定login_process事件
        self.Bind(wx.EVT_BUTTON, self.getlogindata, btn)
        # 将Panmel适应GridBagSizer()放置
        panel.SetSizerAndFit(sizer)

        self.Bind(wx.EVT_CLOSE, self.onExit)  # 绑定“退出”选项的点击事件

    def getlogindata(self, event):
        if self.textinput_pwd.GetValue() == '' \
                or self.textinput_captcha.GetValue() == '' \
                or self.textinput_user.GetValue() == '':
            wx.MessageBox('用户名密码验证码不能为空', "Error")
            return
        gl.set_value('logindata', [True,
                                   {'username': self.textinput_user.GetValue(),
                                    'password': self.textinput_pwd.GetValue(),
                                    'captcha': self.textinput_captcha.GetValue()}])
        self.loginflag[0] = True
        self.Close()

    def onExit(self, event):
        if not self.loginflag[0]:
            gl.set_value('logindata', [False,
                                       {'username': '',
                                        'password': '',
                                        'captcha': ''}])
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
        redirect = True if gl.get_value('config').loglevel == 'debug' else False
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
        gl.set_value('logwindow', self)
        #self.SetTopWindow(self.frame)
        self.frame.Show()
        self.frame.Raise()
        wx.CallLater(1000, self.checkptthread)
        self.setclearlogtimer()
        pub.subscribe(self.updateHandle, "update")
        return True

    def setclearlogtimer(self):
        # 获取现在时间
        now_time = datetime.datetime.now()
        # 获取明天时间
        next_time = now_time + datetime.timedelta(days=+1)
        next_year = next_time.date().year
        next_month = next_time.date().month
        next_day = next_time.date().day
        # 获取明天0点时间
        next_time = datetime.datetime.strptime(
            str(next_year) + "-" + str(next_month) + "-" + str(next_day) + " 00:00:00", "%Y-%m-%d %H:%M:%S")
        # 获取昨天时间
        # last_time = now_time + datetime.timedelta(days=-1)

        # 获取距离明天0点时间，单位为秒
        timer_start_time = int((next_time - now_time).total_seconds() * 1000)
        wx.CallLater(timer_start_time, self.clearlog)

    def clearlog(self):
        # 刷新图标
        self.TaskBar.SetIcon(wx.Icon(self.TaskBar.ICON), self.TaskBar.TITLE)
        self.frame.textctrl.SetValue('')
        # 设置下一次clear定时
        self.setclearlogtimer()

    def checkptthread(self):
        if gl.get_value('thread') is not None and gl.get_value('thread').is_alive():
            # time.sleep(1)
            wx.CallLater(1000, self.checkptthread)
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
