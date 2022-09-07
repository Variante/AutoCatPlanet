# 猫之城小工具集合

这是一个运行在Windows平台上的基于模板匹配及各种简单计算机视觉技术的猫之城自用工具箱。
使用ADB链接到模拟器进行操作，需要在config中适配模拟器的分辨率，并要根据电脑性能决定延迟量。如果不是MuMu模拟器或者不同分辨率还要修改截屏/控制参数。

当前功能包括(按数字键切换):
1. 半自动钓鱼(目前不维护升级及钓鱼耗材)
2. 猫球基因预测(beta)
3. 自动涂鸦一本(beta)


## 安装
```
git clone https://github.com/Variante/AutoCatPlanet
cd AutoCatPlanet
pip install mss pillow scipy numpy opencv-python pywin32 adb-shell
```

猫球查询依赖[CnORC](https://github.com/breezedeus/cnocr)
```
pip install cnocr
```

## 使用前准备
根据模拟器渲染分辨率调整config.json文件中的adb_shape等其它各类参数，
常见的需要修改的内容包括（特别是如果你使用其它的模拟器时）
```
"name": "MuMu模拟器",      # 更改为需要的窗口名称
"padding": [36, 53, 0, 0], # 切除上、下、左、右的黑边，需要调整这4个值使得只有游戏画面被精准捕捉，过多过少都不行。
"autopadding": true,       # 现已支持自动检测padding，在一个明亮的画面下按P即可检测，建议得到结果后修改config
"autopadding_thre": 40,
"adb_shape": [2560, 1440], # 更改为模拟器渲染的分辨率（设置中能看到，不是实际窗口大小）
"adb_device": "/dev/input/event8", # 更改为你模拟器的输入设备，如果不知道输入设备是哪个，使用adb shell getevent后查看
"adb_port": 7555, # 不同的模拟器端口可能不同
```

确保修改后json文件依然格式正确，最后打开模拟器后运行AutoCatPlanet.py即可，使用时需保证游戏窗口在前台。

如果不需要本软件窗口紧贴模拟器，请将config中修改stick为空队列。
```
 "stick": [],
```

如果你为其它模拟器修改好了配置文件，欢迎pr，感谢。

## 使用方法
```
S:保存当前截图
P:在启用autopadding后估计config中padding的数值,建议得到结果后手动更改config.json中的padding
空格:暂停/恢复
Q:退出
--------
数字1: 半自动钓鱼 [默认]
数字2: 猫球基因查询
数字3：自动涂鸦一本
```


### 半自动钓鱼
修改在config中的这个部分来优化你的钓鱼体验

```
"fishing": {
		"circle_predict": 15,  # 抛竿提前量，如果点击时刻比perfect要慢则增大这个值
		"pull_release": 30, # 拉鱼松开按钮的阈值
		"drop_thre": 70, # 已弃用
		"drop_until": 1, # 已弃用
		"drop_cheap_fish": false # 已弃用
	},
```

### 猫球基因预测

修改在config中的这个部分来定制你的查询需求

```
"gene": {
	"blue_score": 2,  # 蓝色基因符合时的得分
	"green_score": 1, # 绿色基因符合时的得分
	"type_score": 1, # 猫种符合时的得分
	
	# 猫球的得分计算方法为： 主题猫种符合得分 + 每个蓝色基因符合得分+ 每个蓝色基因猫种符合得分 + 每个绿色基因符合得分
	
	"display": 5, # 显示的候选主题数量
	"want": [], # 希望特别关注的主题
	"ignore": ["海湾救援"] # 忽略的主题
},
```

### 自动刷涂鸦
首先替换img中的grafffinalbattle.png为你的最终阵容，随后修改在config中的这个部分来选择你的阵容。注意使用graffselect时的武装顺序应为第二场小战斗结束后的武装顺序。后面可能按需增加自动识别位置。

```
"graffiti": {
		"select1": [2, 5], # 选择的第1个武装，在graffselect.png中为第2行，第5列
		"select2": [2, 4], # 选择的第2个武装，在graffselect.png中为第2行，第4列
		"select3": [1, 3], # 以此类推
		"select4": [1, 2] 
	},
},
```
目前的逻辑是两场小战斗后进行boss战，不更改猫球buff，不使用料理。


## 已知问题
* 在和🐟拉扯的时候有概率丢失按键，原因不详。(似乎换了新的adb之后修复了这个问题)
* 猫球基因预测尚在beta，预测基因可能不准确，请不要轻信结果


## 联系
请优先使用issue这样能帮到更多人。


## 声明
本工具仅供娱乐，如果您因为使用本软件造成损失，那可真是太遗憾了。
