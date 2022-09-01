# 猫之城小工具集合

这是一个运行在Windows平台上的基于模板匹配及各种简单计算机视觉技术的猫之城自用工具箱，目前不维护升级及钓鱼耗材。
使用ADB链接到模拟器进行操作，需要在config中适配模拟器的分辨率，并要根据电脑性能决定延迟量。如果不是MuMu模拟器或者不同分辨率还要修改截屏/控制参数。


## 安装
```
git clone https://github.com/Variante/AutoCatPlanet
cd AutoCatPlanet
pip install mss pillow scipy numpy opencv-python pywin32 adb-shell
```

## 使用方法
根据模拟器渲染分辨率调整config.json文件中的adb_shape等其它各类参数，
常见的需要修改的内容包括（特别是如果你使用其它的模拟器时）
```
"name": "MuMu模拟器",      # 更改为需要的窗口名称
"padding": [36, 53, 0, 0], # 切除上、下、左、右的黑边，需要调整这4个值使得只有游戏画面被精准捕捉，过多过少都不行。
"adb_shape": [2560, 1440], # 更改为模拟器渲染的分辨率（设置中能看到，不是实际窗口大小）
"adb_device": "/dev/input/event8", # 更改为你模拟器的输入设备，如果不知道输入设备是哪个，使用adb shell getevent后查看
"adb_port": 7555, # 不同的模拟器端口可能不同
"fishing": {
		"circle_predict": 30, # 如果抛鱼竿时按得总是迟一些导致不能perfect，则增加这个值；否则减小这个值
		"pull_release": 30 
	},
```

确保修改后json文件依然格式正确，最后打开模拟器后运行AutoCatPlanet.py即可，使用时需保证游戏窗口在前台。
```
S:保存图片
空格:暂停及恢复
```
如果你为其它模拟器修改好了配置文件，欢迎pr，感谢。

## 已知问题
在和🐟拉扯的时候有概率丢失按键，原因不详。(似乎换了新的adb之后修复了这个问题)

## 声明
本工具仅供娱乐，如果您因为使用本软件造成损失，那可真是太遗憾了。
