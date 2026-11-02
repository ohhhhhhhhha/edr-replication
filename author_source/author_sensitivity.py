
import matplotlib.pyplot as plt
import control as ct
import numpy as np

from matplotlib.font_manager import FontProperties
宋体 = FontProperties(fname=r"/Users/fangyuanli/Library/Fonts/simsun.ttc", size=12)# 指定本机的字体文件路径【需要在自己本机上找你自己的字体】

保存 = False

w = 1
A = [[0,1],[-w*w,0]]
B = [[0],[1]]
C = [[1,0]]
D = 0
sys = ct.StateSpace(A,B,C,D)

时长 = 5
#引入参考信号p.519
r = 1
K = np.array([[3,4]])
N = 4
#更改系统参数
w=0.5
A_min = [[0,1],[-w*w,0]]
w=1.5
A_max = [[0,1],[-w*w,0]]
#不同的a的影响
aa = np.linspace(0,25)
y1 = []
# 新控制器
for a in aa:
    K_n = np.array([[a*a,0]])
    _, 参变y_min, _ = ct.forced_response(ct.StateSpace(A_min - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)
    _, 参变y_max, _ = ct.forced_response(ct.StateSpace(A_max - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)
    y1.append(参变y_min[-1] - 参变y_max[-1])

w=0.1
A_min = [[0,1],[-w*w,0]]
w=1.9
A_max = [[0,1],[-w*w,0]]
y2 = []
# 新控制器
for a in aa:
    K_n = np.array([[a*a,0]])
    _, 参变y_min, _ = ct.forced_response(ct.StateSpace(A_min - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)
    _, 参变y_max, _ = ct.forced_response(ct.StateSpace(A_max - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)
    y2.append(参变y_min[-1] - 参变y_max[-1])

#绘制系统在仿真终点时，对w=0.5和w=1.5下的变化范围，随a的变化
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(aa,y1,label='$\hat{\omega}_0\in[0.5,1.5]$')
plt.plot(aa,y2,label='$\hat{\omega}_0\in[0.1,1.9]$')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlabel('Variation of $\\alpha$',fontproperties='Times New Roman', size = 12)
plt.ylabel('Steady-state error of $y(x_1)$',fontproperties='Times New Roman', size = 12)
plt.xlim(0,aa[-1])
# plt.ylim(0,1.4)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('var-a.pdf', bbox_inches='tight')
plt.show()