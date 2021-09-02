# coding: utf-8
import json
import os

from app.components.dialogs.select_model_dialog import SelectModelDialog
from app.components.widgets.label import ClickableLabel
from app.components.widgets.scroll_area import ScrollArea
from app.components.widgets.slider import Slider
from app.components.widgets.switch_button import SwitchButton
from PyQt5.QtCore import QFile, Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QLabel, QPushButton, QRadioButton, QWidget
from torch import cuda


class SettingInterface(ScrollArea):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.config = self.__readConfig()
        self.scrollWidget = QWidget(self)

        # 此 PC 上的阿尔法狗
        self.modelInPCLabel = QLabel(
            self.tr('Alpha Gobang in this PC'), self.scrollWidget)
        self.selectModelLabel = ClickableLabel(
            self.tr('Choose where we look for Alpha Gobang'), self.scrollWidget)

        # 显卡
        self.useGPULabel = QLabel(self.tr('Graphics Card'), self.scrollWidget)
        self.useGPUSwitchButton = SwitchButton(parent=self.scrollWidget)
        self.useGPUTipsLabel = QLabel(
            self.tr('Use GPU to speed up Alpha Gobang thinking (if available)'), self.scrollWidget)

        # 先手
        self.firstHandLabel = QLabel(
            self.tr('Offensive Position'), self.scrollWidget)
        self.AIButton = QRadioButton(
            self.tr('Alpha Gobang'), self.scrollWidget)
        self.humanButton = QRadioButton(self.tr('Human'), self.scrollWidget)

        # 蒙特卡洛树
        self.mctsLabel = QLabel(self.tr('Monte Carlo tree'), self.scrollWidget)
        self.mctsIterTimeSlider = Slider(Qt.Horizontal, self.scrollWidget)
        self.cPuctSlider = Slider(Qt.Horizontal, self.scrollWidget)
        self.cPuctLabel = QLabel(
            self.tr('Set exploration constant'), self.scrollWidget)
        self.mctsIterTimeLabel = QLabel(
            self.tr('Set search times'), self.scrollWidget)
        self.cPuctValueLabel = QLabel(
            str(self.config.get('c_puct', 40)), self.scrollWidget)
        self.mctsIterTimeValueLabel = QLabel(
            str(self.config.get('n_mcts_iters', 1500)), self.scrollWidget)

        # 关于此应用
        self.aboutAppLabel = QLabel(
            self.tr('About this App'), self.scrollWidget)
        self.giveIssueButton = QPushButton(
            self.tr('Send feedback'), self.scrollWidget)
        self.appInfoLabel = QLabel('Alpha Gobang Zero v1.0', self.scrollWidget)

        self.__initWidget()

    def __initWidget(self):
        """ 初始化界面 """
        self.resize(700, 700)
        self.scrollWidget.resize(540, 760)
        self.cPuctValueLabel.setMinimumWidth(50)
        self.setWidget(self.scrollWidget)

        # 选择模型文件
        self.modelInPCLabel.move(30, 30)
        self.selectModelLabel.move(30, 78)

        # 使用 GPU 加速
        self.useGPULabel.move(30, 138)
        self.useGPUTipsLabel.move(30, 180)
        self.useGPUSwitchButton.move(30, 210)

        # 先手后手
        self.firstHandLabel.move(30, 270)
        self.humanButton.move(30, 315)
        self.AIButton.move(30, 360)

        # 蒙特卡洛树参数
        self.mctsLabel.move(30, 420)
        self.cPuctLabel.move(30, 466)
        self.cPuctSlider.move(30, 496)
        self.cPuctValueLabel.move(230, 496)
        self.mctsIterTimeLabel.move(30, 530)
        self.mctsIterTimeSlider.move(30, 560)
        self.mctsIterTimeValueLabel.move(230, 560)

        # 关于此应用
        self.aboutAppLabel.move(30, 620)
        self.appInfoLabel.move(30, 662)
        self.giveIssueButton.move(30, 700)

        # 初始化 GPU 复选框
        isUseGPU = self.config.get('is_use_gpu', False) and cuda.is_available()
        self.useGPUSwitchButton.setText(
            self.tr('On') if isUseGPU else self.tr('Off'))
        self.useGPUSwitchButton.setChecked(isUseGPU)
        self.useGPUSwitchButton.setEnabled(cuda.is_available())

        # 初始化滑动条
        self.cPuctSlider.setRange(5, 200)
        self.cPuctSlider.setSingleStep(5)
        self.mctsIterTimeSlider.setSingleStep(50)
        self.mctsIterTimeSlider.setRange(400, 4000)
        self.cPuctSlider.setValue(10*self.config.get('c_puct', 4))
        self.mctsIterTimeSlider.setValue(self.config.get('n_mcts_iters', 1500))

        # 初始化先手单选框
        isHumanFirst = self.config.get('is_human_first', True)
        self.humanButton.setChecked(isHumanFirst)
        self.AIButton.setChecked(not isHumanFirst)

        # 设置层叠样式
        self.__setQss()
        # 信号连接到槽
        self.__connectSignalToSlot()

    def __setQss(self):
        """ 设置层叠样式 """
        self.mctsLabel.setObjectName('titleLabel')
        self.useGPULabel.setObjectName('titleLabel')
        self.aboutAppLabel.setObjectName('titleLabel')
        self.firstHandLabel.setObjectName('titleLabel')
        self.modelInPCLabel.setObjectName('titleLabel')
        self.selectModelLabel.setObjectName("clickableLabel")

        f = QFile(':/qss/setting_interface.qss')
        f.open(QFile.ReadOnly)
        self.setStyleSheet(str(f.readAll(), encoding='utf-8'))
        f.close()

    def __readConfig(self) -> dict:
        """ 读入配置 """
        self.__checkDir()
        if not os.path.exists('app/config/config.json'):
            config = {
                "c_puct": 4,
                "is_use_gpu": False,
                "n_mcts_iters": 1500,
                "is_human_first": True,
                "model": "model\\best_policy_value_net.pth"
            }
            return config

        with open('app/config/config.json', encoding='utf-8') as f:
            return json.load(f)

    def __checkDir(self):
        """ 检查配置文件夹是否存在 """
        if not os.path.exists('app/config'):
            os.mkdir('app/config')

    def __showSelectModelDialog(self):
        """ 显示选择模型对话框 """
        dialog = SelectModelDialog(self.config['model'], self.window())
        dialog.modelChangedSignal.connect(self.__modelChangedSlot)
        dialog.exec_()

    def __connectSignalToSlot(self):
        """ 信号连接到槽 """
        self.cPuctSlider.valueChanged.connect(self.__adjustCPuct)
        self.selectModelLabel.clicked.connect(self.__showSelectModelDialog)
        self.useGPUSwitchButton.checkedChanged.connect(
            self.__useGPUChangedSlot)
        self.humanButton.clicked.connect(self.__firstHandChangedSlot)
        self.AIButton.clicked.connect(self.__firstHandChangedSlot)
        self.mctsIterTimeSlider.valueChanged.connect(
            self.__adjustMctsIterTimer)
        self.giveIssueButton.clicked.connect(lambda: QDesktopServices.openUrl(
            QUrl('https://github.com/zhiyiYo/Alpha-Gobang-Zero/issues')))

    def __modelChangedSlot(self, model: str):
        """ 模型改变信号槽函数 """
        if model != self.config['model']:
            self.config['model'] = model

    def __useGPUChangedSlot(self):
        """ 使用 GPU 加速复选框选中状态改变槽函数 """
        isUse = self.useGPUSwitchButton.isChecked()
        self.config['is_use_gpu'] = isUse
        self.useGPUSwitchButton.setText(self.tr('On') if isUse else self.tr('Off'))

    def __firstHandChangedSlot(self):
        """ 先手改变 """
        self.config['is_human_first'] = self.humanButton.isChecked()

    def __adjustCPuct(self, cPuct: float):
        """ 调整探索常数槽函数 """
        self.config['c_puct'] = cPuct/10
        self.cPuctValueLabel.setText(str(cPuct/10))

    def __adjustMctsIterTimer(self, iterTime: int):
        """ 调整蒙特卡洛树搜索次数槽函数 """
        self.config['n_mcts_iters'] = iterTime
        self.mctsIterTimeValueLabel.setNum(iterTime)

    def saveConfig(self):
        """ 保存设置 """
        self.__checkDir()
        with open('app/config/config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f)