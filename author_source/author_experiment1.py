#!/usr/bin/env python
import matplotlib.pyplot as plt
import control as ct
import numpy as np

from matplotlib.font_manager import FontProperties
宋体 = FontProperties(fname=r"/Users/fangyuanli/Library/Fonts/simsun.ttc", size=12)# 指定本机的字体文件路径【需要在自己本机上找你自己的字体】

保存 = True

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
参环t, 参环y, 参环x = ct.forced_response(ct.StateSpace(A - B @ K, B, C, D),T=np.linspace(0, 时长, 1000),U=N*r,return_x=True)#均值系统
参变t, 参变y, 参变x_min = ct.forced_response(ct.StateSpace(A_min - B @ K, B, C, D),T=np.linspace(0, 时长, 1000),U=N*r,return_x=True)#减小固有频率
参变t, 参变y, 参变x_max = ct.forced_response(ct.StateSpace(A_max - B @ K, B, C, D),T=np.linspace(0, 时长, 1000),U=N*r,return_x=True)#增大固有频率
#新控制器参数
a = 2
K_n = np.array([[a*a,0]])
#新控制器
参环t, 参环y, 参环x_n = ct.forced_response(ct.StateSpace(A - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)
参变t, 参变y, 参变x_min_n = ct.forced_response(ct.StateSpace(A_min - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)
参变t, 参变y, 参变x_max_n = ct.forced_response(ct.StateSpace(A_max - B@(K+K_n), B, C, D),T=np.linspace(0, 时长, 1000),U=(N+a*a)*r,return_x=True)

#绘制理想系统的控制
#绘制x1
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(参环t, 参环x[0,:], label='Con. Ref.')
plt.plot(参环t, 参环x_n[0,:], label='Var. Ref.')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlabel('Time(sec)',fontproperties='Times New Roman', size = 12)
plt.ylabel('Amplitude of $y(x_1)$',fontproperties='Times New Roman', size = 12)
plt.xlim(0,时长)
plt.ylim(0,1.4)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('Ideal-x1.pdf', bbox_inches='tight')
plt.show()
#绘制x2
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(参环t, 参环x[1,:], label='Con. Ref.')
plt.plot(参环t, 参环x_n[1,:], label='Var. Ref.')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlabel('Time(sec)',fontproperties='Times New Roman', size = 12)
plt.ylabel('Amplitude of $x_2$',fontproperties='Times New Roman', size = 12)
plt.xlim(0,时长)
# plt.ylim(0,1.4)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('Ideal-x2.pdf', bbox_inches='tight')
plt.show()

#绘制不一致系统的控制
#绘制原始控制器的x1
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(参变t, 参变x_min[0,:], label='$\hat{\omega}_0=0.5$')
plt.plot(参变t, 参变x_max[0,:], label='$\hat{\omega}_0=1.5$')
plt.fill_between(参变t, 参变x_min[0,:], 参变x_max[0,:], color='gray', alpha=0.3, label='Range of Variation')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlabel('Time(sec)',fontproperties='Times New Roman', size = 12)
plt.ylabel('Amplitude of $y(x_1)$',fontproperties='Times New Roman', size = 12)
plt.xlim(0,时长)
plt.ylim(0,1.4)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('ConRef-x1.pdf', bbox_inches='tight')
plt.show()
#绘制原始控制器的x2
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(参变t, 参变x_min[1,:], label='$\hat{\omega}_0=0.5$')
plt.plot(参变t, 参变x_max[1,:], label='$\hat{\omega}_0=1.5$')
plt.fill_between(参变t, 参变x_min[1,:], 参变x_max[1,:], color='gray', alpha=0.3, label='Range of Variation')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlim(0,时长)
plt.ylim(0,0.8)
plt.xlabel('Time(sec)',fontproperties='Times New Roman', size = 12)
plt.ylabel('Amplitude of state $x_2$',fontproperties='Times New Roman', size = 12)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('ConRef-x2.pdf', bbox_inches='tight')
plt.show()
#绘制新控制器的x1
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(参变t, 参变x_min_n[0,:], label='Var. Ref., $\hat{\omega}_0=0.5$')
plt.plot(参变t, 参变x_max_n[0,:], label='$Var. Ref., \hat{\omega}_0=1.5$')
plt.plot(参变t, 参变x_min[0,:], label='Con. Ref., $\hat{\omega}_0=0.5$', linestyle='--')
plt.plot(参变t, 参变x_max[0,:], label='Con. Ref., $\hat{\omega}_0=1.5$', linestyle='--')
plt.fill_between(参变t, 参变x_min[0,:], 参变x_max[0,:], color='gray', alpha=0.3)
plt.fill_between(参变t, 参变x_min_n[0,:], 参变x_max_n[0,:], color='green', alpha=0.3, label='Range of Variation')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlabel('Time(sec)',fontproperties='Times New Roman', size = 12)
plt.ylabel('Amplitude of $y(x_1)$',fontproperties='Times New Roman', size = 12)
plt.xlim(0,时长)
plt.ylim(0,1.4)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('VarRef-x1.pdf', bbox_inches='tight')
plt.show()
#绘制新控制器的x2
plt.figure(figsize=(6,4))# 设置绘图的宽、高，默认英寸
plt.plot(参变t, 参变x_min_n[1,:], label='Var. Ref., $\hat{\omega}_0=0.5$')
plt.plot(参变t, 参变x_max_n[1,:], label='Var. Ref., $\hat{\omega}_0=1.5$')
plt.plot(参变t, 参变x_min[1,:], label='Con. Ref., $\hat{\omega}_0=0.5$', linestyle='--')
plt.plot(参变t, 参变x_max[1,:], label='Con. Ref., $\hat{\omega}_0=1.5$', linestyle='--')

plt.fill_between(参变t, 参变x_min[1,:], 参变x_max[1,:], color='gray', alpha=0.3)
plt.fill_between(参变t, 参变x_min_n[1,:], 参变x_max_n[1,:], color='green', alpha=0.3, label='Range of Variation')
plt.xticks(fontproperties = 'Times New Roman', size = 12)
plt.yticks(fontproperties = 'Times New Roman', size = 12)
plt.xlim(0,时长)
# plt.ylim(0,0.8)
plt.xlabel('Time(sec)',fontproperties='Times New Roman', size = 12)
plt.ylabel('Amplitude of state $x_2$',fontproperties='Times New Roman', size = 12)
plt.legend()
plt.grid(True)
if 保存:
    plt.savefig('VarRef-x2.pdf', bbox_inches='tight')
plt.show()

